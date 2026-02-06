import enum
import urllib.parse

import models

class ProxyType(enum.Enum):
    HTTP = enum.auto()
    HTTPS = enum.auto()


class Client:
    def __init__(self, proxies: dict[ProxyType, str] | None = None) -> None:
        self.proxies = dict()
        if proxies is None:
            return
        for proxy_type, url in proxies.items():
            result = urllib.parse.urlparse(url)
            if result.scheme in ("http", "https") and result.netloc:
                match proxy_type:
                    case ProxyType.HTTP:
                        self.proxies.update(http=url)
                    case ProxyType.HTTPS:
                        self.proxies.update(https=url)
            else:
                raise ValueError("Please use a valid proxy URL!")
            
    async def get_user(self, userid: int) -> models.User:
        return await models.User.new(userid, self.proxies)
