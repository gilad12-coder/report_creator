"""
Stage 2: Hierarchical tree summarization with map-reduce pattern.

Implements 3-level tree structure:
- Leaf: 10 facts → 200-token local abstract (extraction-heavy)
- Branch: 10 leafs → 400-token summary (pattern-focused)
- Root: 1 branch → 800-token final digest (analytic)

Uses SliSum sliding window + self-consistency at leaf level to reduce hallucinations.
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Tuple
from tqdm import tqdm
from opentelemetry import trace

from src.utils.config import LEAF_TEMPLATE, BRANCH_TEMPLATE, ROOT_TEMPLATE, LEAF_SIZE, BRANCH_SIZE
from src.utils.utils import chat_completion, format_facts_for_display

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class QueryLevel(Enum):
    """Query classification levels for hierarchical tree navigation."""
    STRATEGIC = "strategic"
    PATTERN = "pattern"
    SPECIFIC = "specific"
    MIXED = "mixed"


@dataclass
class DigestTree:
    """Hierarchical digest tree structure preserving all levels."""
    facts: List[Dict[str, Any]]
    leafs: List[str]
    branches: List[str]
    root: str
    leaf_fact_mapping: Dict[int, List[int]]  # leaf_id -> [fact_indices]
    branch_leaf_mapping: Dict[int, List[int]]  # branch_id -> [leaf_indices]


class DigestLayer:
    """
    Creates hierarchical digest tree using map-reduce pattern.

    Processes facts through multiple levels:
    - Leaf level: Local abstracts from small fact groups
    - Branch level: Pattern summaries from leaf abstracts
    - Root level: Strategic digest from branch summaries
    """

    def digest_facts(self, facts: List[Dict[str, Any]]) -> DigestTree:
        """
        Create hierarchical digest tree using map-reduce pattern.

        Args:
            facts: List of fact dictionaries to digest

        Returns:
            Complete DigestTree structure with all levels and mappings
        """
        with tracer.start_as_current_span("hierarchical_digest_stage") as span:
            if not facts:
                span.set_attribute("digest.result", "no_facts")
                return DigestTree(
                    facts=[],
                    leafs=[],
                    branches=[],
                    root="No facts available for digestion.",
                    leaf_fact_mapping={},
                    branch_leaf_mapping={}
                )

            span.set_attribute("input.fact_count", len(facts))
            span.set_attribute("digest.method", "hierarchical_tree")

            logger.info(f"Starting hierarchical digest of {len(facts)} facts")

            leafs, leaf_fact_mapping = self._create_leaf_abstracts(facts)
            span.set_attribute("leaf.abstracts_created", len(leafs))

            if len(leafs) <= 1:
                return DigestTree(
                    facts=facts,
                    leafs=leafs,
                    branches=[],
                    root=leafs[0] if leafs else "Insufficient facts for hierarchical processing.",
                    leaf_fact_mapping=leaf_fact_mapping,
                    branch_leaf_mapping={}
                )

            branches, branch_leaf_mapping = self._create_branch_summaries(leafs)
            span.set_attribute("branch.summaries_created", len(branches))

            if len(branches) <= 1:
                return DigestTree(
                    facts=facts,
                    leafs=leafs,
                    branches=branches,
                    root=branches[0] if branches else leafs[0],
                    leaf_fact_mapping=leaf_fact_mapping,
                    branch_leaf_mapping=branch_leaf_mapping
                )

            root_digest = self._create_root_digest(branches)

            span.set_attribute("output.digest_length", len(root_digest))
            span.set_attribute("digest.result", "success")
            logger.info(f"Generated hierarchical digest tree")

            return DigestTree(
                facts=facts,
                leafs=leafs,
                branches=branches,
                root=root_digest,
                leaf_fact_mapping=leaf_fact_mapping,
                branch_leaf_mapping=branch_leaf_mapping
            )

    def _create_leaf_abstracts(self, facts: List[Dict[str, Any]]) -> Tuple[List[str], Dict[int, List[int]]]:
        """
        Create leaf-level abstracts using SliSum sliding window approach.

        Args:
            facts: List of fact dictionaries

        Returns:
            Tuple of (leaf abstracts, leaf-to-fact mapping)
        """
        abstracts = []
        leaf_fact_mapping = {}
        total_leaves = (len(facts) + LEAF_SIZE - 1) // LEAF_SIZE

        with tqdm(total=total_leaves, desc="Creating leaf abstracts", unit="leaf") as pbar:
            for i in range(0, len(facts), LEAF_SIZE):
                leaf_facts = facts[i:i + LEAF_SIZE]
                leaf_id = len(abstracts)
                fact_indices = list(range(i, min(i + LEAF_SIZE, len(facts))))
                leaf_fact_mapping[leaf_id] = fact_indices

                if len(leaf_facts) >= 3:
                    abstract = self._slisum_leaf_abstract(leaf_facts)
                else:
                    abstract = self.simple_leaf_abstract(leaf_facts)

                abstracts.append(abstract)
                pbar.update(1)

        return abstracts, leaf_fact_mapping

    def _slisum_leaf_abstract(self, facts: List[Dict[str, Any]]) -> str:
        """
        Apply SliSum sliding window + self-consistency to leaf facts.

        Args:
            facts: Leaf-level facts (typically 10 facts)

        Returns:
            Consensus abstract from sliding windows
        """
        if len(facts) < 5:
            return self.simple_leaf_abstract(facts)

        window_size = min(7, len(facts))
        overlap = window_size // 2
        window_abstracts = []

        for start in range(0, len(facts) - window_size + 1, overlap):
            end = start + window_size
            window_facts = facts[start:end]
            abstract = self.simple_leaf_abstract(window_facts)
            window_abstracts.append(abstract)

        if len(window_abstracts) <= 1:
            return window_abstracts[0] if window_abstracts else self.simple_leaf_abstract(facts)

        consensus_prompt = f"""
        These are {len(window_abstracts)} overlapping abstracts of the same intelligence facts.
        Create a consensus 200-token abstract that preserves the most consistent and reliable information:

        {chr(10).join(f"Abstract {i + 1}: {abstract}" for i, abstract in enumerate(window_abstracts))}

        Consensus Abstract (200 tokens max):
        """

        messages = [{"role": "user", "content": consensus_prompt}]
        consensus = chat_completion(
            messages,
            max_tokens=250,
            temperature=0.1,
            operation_name="slisum_consensus",
            use_premium=False
        )

        return consensus

    @staticmethod
    def simple_leaf_abstract(facts: List[Dict[str, Any]]) -> str:
        """
        Create simple leaf abstract without sliding window.

        Args:
            facts: Facts to abstract

        Returns:
            Leaf abstract string
        """
        formatted_facts = format_facts_for_display(facts)
        prompt = LEAF_TEMPLATE.render(
            fact_count=len(facts),
            formatted_facts=formatted_facts
        )

        messages = [{"role": "user", "content": prompt}]
        abstract = chat_completion(
            messages,
            max_tokens=250,
            temperature=0.1,
            operation_name="leaf_abstract",
            use_premium=False
        )

        return abstract

    @staticmethod
    def _create_branch_summaries(abstracts: List[str]) -> Tuple[List[str], Dict[int, List[int]]]:
        """
        Create branch-level summaries from leaf abstracts.

        Args:
            abstracts: List of leaf abstracts

        Returns:
            Tuple of (branch summaries, branch-to-leaf mapping)
        """
        summaries = []
        branch_leaf_mapping = {}

        for i in range(0, len(abstracts), BRANCH_SIZE):
            branch_abstracts = abstracts[i:i + BRANCH_SIZE]
            branch_id = len(summaries)
            leaf_indices = list(range(i, min(i + BRANCH_SIZE, len(abstracts))))

            branch_leaf_mapping[branch_id] = leaf_indices

            prompt = BRANCH_TEMPLATE.render(
                abstract_count=len(branch_abstracts),
                abstracts="\n\n".join(f"Abstract {j + 1}:\n{abstract}"
                                      for j, abstract in enumerate(branch_abstracts))
            )

            messages = [{"role": "user", "content": prompt}]
            summary = chat_completion(
                messages,
                max_tokens=500,
                temperature=0.1,
                operation_name="branch_summary",
                use_premium=False
            )

            summaries.append(summary)

        return summaries, branch_leaf_mapping

    @staticmethod
    def _create_root_digest(summaries: List[str]) -> str:
        """
        Create final root digest from branch summaries.

        Args:
            summaries: List of branch summaries

        Returns:
            Final root digest string
        """
        prompt = ROOT_TEMPLATE.render(
            summaries="\n\n".join(f"Branch {i + 1}:\n{summary}"
                                  for i, summary in enumerate(summaries))
        )

        messages = [{"role": "user", "content": prompt}]
        digest = chat_completion(
            messages,
            max_tokens=900,
            temperature=0.1,
            operation_name="root_digest",
            use_premium=False
        )

        return digest