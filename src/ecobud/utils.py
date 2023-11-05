from typing import Any, Dict, List, Union

import curlify  # type: ignore [import-untyped]
from requests import Response

JSONType = Union[None, bool, str, float, int, List["JSONType"], Dict[str, "JSONType"]]
JSONDict = Dict[str, JSONType]
JSONList = List[JSONType]
JSONRoot = Union[JSONDict, JSONList]


def curl(response: Response) -> str:
    return curlify.to_curl(response.request)


def fmt_response(response: Response) -> str:
    if response.status_code == 200:
        return response.json()
    else:
        return f"<{response.status_code}>: {response.text}"
