from dataclasses import dataclass, field


@dataclass
class QueryEntity:
    """Pure domain entity for a Query. No infrastructure dependencies."""

    id: str
    full_query: str
    collections: list[str] = field(default_factory=list)
    highlighted_words: list[str] = field(default_factory=list)
    solution_id: str = ""

    # ------------------------------------------------------------------ #
    # Factory Methods
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        id: str,
        full_query: str,
        solution_id: str,
        collections: list[str] = None,
        highlighted_words: list[str] = None,
    ) -> "QueryEntity":
        """Create a new query."""
        if not full_query or not full_query.strip():
            raise ValueError("full_query cannot be empty")
        if len(full_query) > 10000:
            raise ValueError("full_query cannot exceed 10000 characters")
        if not solution_id:
            raise ValueError("Solution ID is required")
        if not id:
            raise ValueError("Query ID is required")

        return cls(
            id=id,
            full_query=full_query.strip(),
            collections=collections or [],
            highlighted_words=highlighted_words or [],
            solution_id=solution_id,
        )

    # ------------------------------------------------------------------ #
    # Business Mutation Methods
    # ------------------------------------------------------------------ #

    def update_query(self, full_query: str) -> None:
        """Update the full query text."""
        if not full_query or not full_query.strip():
            raise ValueError("full_query cannot be empty")
        if len(full_query) > 10000:
            raise ValueError("full_query cannot exceed 10000 characters")
        self.full_query = full_query.strip()

    def update_collections(self, collections: list[str]) -> None:
        """Update the collections list."""
        if collections is None:
            self.collections = []
        else:
            self.collections = [c.strip() for c in collections if c and c.strip()]

    def update_highlighted_words(self, highlighted_words: list[str]) -> None:
        """Update the highlighted words list."""
        if highlighted_words is None:
            self.highlighted_words = []
        else:
            self.highlighted_words = [w.strip() for w in highlighted_words if w and w.strip()]

    def add_collection(self, collection: str) -> None:
        """Add a single collection if not already present."""
        if collection and collection.strip() and collection.strip() not in self.collections:
            self.collections.append(collection.strip())

    def remove_collection(self, collection: str) -> bool:
        """Remove a collection. Returns True if removed."""
        if collection in self.collections:
            self.collections.remove(collection)
            return True
        return False

    def add_highlighted_word(self, word: str) -> None:
        """Add a highlighted word if not already present."""
        if word and word.strip() and word.strip() not in self.highlighted_words:
            self.highlighted_words.append(word.strip())

    def remove_highlighted_word(self, word: str) -> bool:
        """Remove a highlighted word. Returns True if removed."""
        if word in self.highlighted_words:
            self.highlighted_words.remove(word)
            return True
        return False