from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
import re
import subprocess
from typing import Iterator

REX_COMMIT = re.compile(
    (
        r'(?P<hash>[0-9a-f]{40}) '
        r'(?P<created_at>[0-9T:+-]+)\s+'
        r'.+ \| \d+ [+-]+\s+'
        r'\d+ files? changed'
        r'(?:, (?P<insertions>\d+) insertions?\(\+\))?'
        r'(?:, (?P<deletions>\d+) deletions?\(\-\))?'
    ),
    re.MULTILINE
)


@dataclass
class Commit:
    path: Path
    hash: str
    created_at: datetime
    insertions: int
    deletions: int

    @cached_property
    def lines_count(self) -> int:
        cmd = ['git', 'show', f'{self.hash}:{self.path}']
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        result.check_returncode()
        lines = result.stdout.decode().strip().splitlines()
        return len(lines)

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result['lines_count'] = self.lines_count
        return result


def get_commits(path: Path) -> Iterator[Commit]:
    cmd = ['git', 'log', '--format=%H %cI', '--stat', '--', str(path)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    result.check_returncode()
    stdout = result.stdout.decode()
    for match in REX_COMMIT.finditer(stdout):
        info = match.groupdict()
        yield Commit(
            path=path,
            hash=info['hash'],
            created_at=datetime.fromisoformat(info['created_at']),
            insertions=int(info['insertions'] or '0'),
            deletions=int(info['deletions'] or '0'),
        )
