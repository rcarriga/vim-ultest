from typing import Callable, Generic, Iterator, List, Optional, Protocol, TypeVar

TreeData = TypeVar("TreeData")


C = TypeVar("C")


class Comparabale(Protocol):
    def __gt__(self: C, x: C) -> bool:
        ...

    def __lt__(self: C, x: C) -> bool:
        ...

    def __eq__(self, x) -> bool:
        ...


SearchKey = TypeVar("SearchKey", bound=Comparabale)


class Tree(Generic[TreeData]):
    def __init__(self, data: TreeData, children: List["Tree[TreeData]"]) -> None:
        self._children: List[Tree[TreeData]] = children
        self._data = data
        self._length = 1 + sum(len(child) for child in self._children)

    @classmethod
    def from_list(cls, data) -> "Tree[TreeData]":
        """
        Parses a tree in the shape of nested lists.

        The head of the list is the root of the tree, and all following elements are its children.
        """
        if isinstance(data, List):
            node_data = data[0]
            children = [cls.from_list(child_data) for child_data in data[1:]]

            return Tree(data=node_data, children=children)
        else:
            return Tree(data=data, children=[])

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> TreeData:
        orig = index
        if index > len(self):
            raise IndexError(f"No node found with index {orig}")

        if index == 0:
            return self._data

        checked = 1
        for child in self._children:
            if len(child) > index - checked:
                return child[index - checked]
            checked += len(child)

        raise Exception  # Shouldn't happen

    def to_list(self):
        if not self._children:
            return [self._data]
        return self._to_list()

    def _to_list(self):
        if not self._children:
            return self._data
        return [self._data, *[child._to_list() for child in self._children]]

    @property
    def data(self) -> TreeData:
        return self._data

    def children(self) -> List["Tree"]:
        return self._children

    def __iter__(self) -> Iterator[TreeData]:
        yield self._data
        for child in self._children:
            for data in child:
                yield data

    def nodes(self) -> Iterator["Tree[TreeData]"]:
        yield self
        for child in self._children:
            for data in child.nodes():
                yield data

    def node(self, index: int) -> "Tree[TreeData]":
        orig = index
        if index > len(self):
            raise IndexError(f"No node found with index {orig}")

        if index == 0:
            return self

        checked = 1
        for child in self._children:
            if len(child) > index - checked:
                return child.node(index - checked)
            checked += len(child)

        raise Exception  # Shouldn't happen

    X = TypeVar("X")

    def map(self, f: Callable[[TreeData], X]) -> "Tree[X]":
        try:
            return Tree(
                data=f(self._data), children=[child.map(f) for child in self._children]
            )
        except Exception:
            breakpoint()
            raise

    def sorted_search(
        self,
        target: SearchKey,
        key: Callable[[TreeData], SearchKey],
        strict: bool = False,
    ) -> Optional["Tree[TreeData]"]:
        """
        Search through the tree using binary search to search through children

        :param target: The target value to find
        :param key: Function to return a value to sort nodes with
        :param strict: The search will only return an exact match, defaults to False
        :return:  The matching node, or nearest one if not strict
        """
        l = 0
        r = len(self) - 1
        while l <= r:
            m = int((l + r) / 2)
            mid = self.node(m)
            if key(mid.data) < target:
                l = m + 1
            elif key(mid.data) > target:
                r = m - 1
            else:
                return mid

        if r < 0:
            return None

        return self.node(r) if not strict and key(self[r]) < target else None
