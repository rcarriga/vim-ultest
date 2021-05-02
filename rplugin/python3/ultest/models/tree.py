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

    def to_list(self):
        if not self._children:
            return self._data
        return [self._data, *[child.to_list() for child in self._children]]

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

    def sorted_search(
        self,
        target: SearchKey,
        key: Callable[[TreeData], SearchKey],
        strict: bool = False,
    ) -> Optional[TreeData]:
        """
        Search through the tree using binary search to search through children

        The tree must be constructed by sorted input

        :param target: The target value to find
        :param key: Function to return a value to sort nodes with
        :param strict: The search will only return an exact match, defaults to False
        :return:  The matching node, or nearest one if not strict
        """
        if not self._children:
            return self._data if not strict else None

        nodes: List[Tree[TreeData]] = [self, *self._children]
        l = 0
        r = len(nodes) - 1
        while l <= r:
            m = int((l + r) / 2)
            mid = nodes[m]
            if key(mid.data) < target:
                l = m + 1
            elif key(mid.data) > target:
                r = m - 1
            else:
                return mid.data

        if r < 0:
            return None

        if r != 0:
            child_result = nodes[r].sorted_search(target=target, key=key, strict=strict)
            if child_result:
                return child_result

        return nodes[r].data if not strict and key(nodes[r].data) < target else None
