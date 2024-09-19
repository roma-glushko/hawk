# Copyright (c) 2024 Roman Hlushko and various contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from hawk.zpages import ZPage
from hawk.zpages.exceptions import ZPageNotFound

RESERVED_ROUTE_PREFIXES: list[str] = [
    "/prof/",
]

ZPAGES: dict[str, ZPage] = {}
"""
The ZPages registry.
"""

def get_pages() -> dict[str, ZPage]:
    """
    Get all registered ZPages.
    """
    return ZPAGES

def get_page_routes() -> list[str]:
    """
    Get all registered ZPage routes.
    """
    return list(ZPAGES.keys())

def get_page(route: str) -> ZPage:
    """
    Get a ZPage by route.

    Raises:
        ZPageNotFound: When the route is not found.
    """
    try:
        return ZPAGES[route]
    except KeyError:
        raise ZPageNotFound(f"ZPage with route '{route}' not found.")

def add_page(route: str, page: ZPage) -> None:
    """
    Add a new route to the ZPages.

    The page route is relative to the Hawk router mount path (e.g. `/debug/` by default).

    Raises:
        ValueError: When the route is in the reserved route namespace.
    """
    for route_prefix in RESERVED_ROUTE_PREFIXES:
        if route.startswith(route_prefix):
            raise ValueError(
                f"Route '{route}' is in the reserved route namespace '{route_prefix}'. "
                f"Please choose a different route."
            )

    ZPAGES[route] = page