from __future__ import annotations
import dataclasses
import typing
import urllib.parse
import gzip
import io
import json
import collections.abc
import datetime
import xml.etree.ElementTree

import httpx
import defusedxml.ElementTree

import client

NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclasses.dataclass
class User:
    name: str
    userid: int
    read: str
    novel_cnt: int
    review_cnt: int
    novel_length: int
    sum_global_point: int

    @classmethod
    async def new(
        cls, userid: int, proxies: dict[str, str] | None = None
    ) -> typing.Self:
        async with httpx.AsyncClient(proxy=proxies) as c:
            params = {
                "gzip": 5,
                "out": "json",
                "of": "n-y-nc-rc-nl-sg",
                "userid": userid,
            }
            response = await c.get(
                "https://api.syosetu.com/userapi/api?{}".format(
                    urllib.parse.urlencode(params)
                )
            )
            response.raise_for_status()
            text = gzip.GzipFile(fileobj=io.BytesIO(response.content)).read().decode()
            data = json.loads(text)[1]
            return cls(
                data["name"],
                userid,
                data["yomikata"],
                data["novel_cnt"],
                data["review_cnt"],
                data["novel_length"],
                data["sum_global_point"],
            )

    async def get_blog(
        self, proxies: dict[str, str] | None = None
    ) -> Blog:
        return await Blog.new(self, proxies)

    async def get_novel(
        self, proxies: dict[str, str] | None = None
    ) -> Novel:
        return await Novel.new(self, proxies)


@dataclasses.dataclass
class Blog:
    author: User
    title: str
    subtitle: str
    entries: collections.abc.Sequence[BlogEntry]

    @classmethod
    async def new(
        cls, user: int | User, proxies: dict[str, str] | None = None
    ) -> typing.Self:
        async with httpx.AsyncClient(proxy=proxies) as c:
            if isinstance(user, int):
                response = await c.get(
                    f"https://api.syosetu.com/writerblog/{user}.Atom"
                )
                user = await User.new(user, proxies)
            else:
                response = await c.get(
                    f"https://api.syosetu.com/writerblog/{user.userid}.Atom"
                )
            response.raise_for_status()
            content = defusedxml.ElementTree.fromstring(response.content)
            entries = list()
            for entry in content.findall("atom:entry", NS):
                entries.append(BlogEntry.new(entry))
            return cls(
                user,
                content.find("atom:title", NS).text,
                content.find("atom:subtitle", NS).text,
                entries,
            )


@dataclasses.dataclass
class BlogEntry:
    title: str
    summary: str
    published: datetime.datetime
    updated: datetime.datetime
    entryid: int

    @classmethod
    def new(cls, entry: xml.etree.ElementTree.Element[str]) -> typing.Self:
        return cls(
            entry.find("atom:title", NS).text,
            entry.find("atom:summary", NS).text,
            datetime.datetime.fromisoformat(entry.find("atom:published", NS).text),
            datetime.datetime.fromisoformat(entry.find("atom:updated", NS).text),
            int(urllib.parse.urlparse(entry.find("atom:id", NS).text).path.split("/")[-1]),
        )


@dataclasses.dataclass
class Novel:
    author: User
    title: str
    subtitle: str
    updated: datetime.datetime
    entries: collections.abc.Sequence[NovelEntry]

    @classmethod
    async def new(
        cls, user: int | User, proxies: dict[str, str] | None = None
    ) -> typing.Self:
        async with httpx.AsyncClient(proxy=proxies) as c:
            if isinstance(user, int):
                response = await c.get(
                    f"https://api.syosetu.com/writernovel/{user}.Atom"
                )
                user = await User.new(user, proxies)
            else:
                response = await c.get(
                    f"https://api.syosetu.com/writernovel/{user.userid}.Atom"
                )
            response.raise_for_status()
            content = defusedxml.ElementTree.fromstring(response.content)
            entries = list()
            for entry in content.findall("atom:entry", NS):
                entries.append(NovelEntry.new(entry))
            return cls(
                user,
                content.find("atom:title", NS).text,
                content.find("atom:subtitle", NS).text,
                datetime.datetime.fromisoformat(content.find("atom:updated", NS).text),
                entries,
            )


@dataclasses.dataclass
class NovelEntry:
    title: str
    summary: str
    published: datetime.datetime
    updated: datetime.datetime
    link: str

    @classmethod
    def new(cls, entry: xml.etree.ElementTree.Element[str]) -> typing.Self:
        return cls(
            entry.find("atom:title", NS).text,
            entry.find("atom:summary", NS).text,
            datetime.datetime.fromisoformat(entry.find("atom:published", NS).text),
            datetime.datetime.fromisoformat(entry.find("atom:updated", NS).text),
            entry.find("atom:link", NS).attrib.get("href"),
        )
