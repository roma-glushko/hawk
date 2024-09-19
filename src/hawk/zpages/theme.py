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
from enum import Enum


class ThemeColor(str, Enum):
    """
    Ref: https://picocss.com/docs/version-picker/red
    """
    RED = "red"
    PINK = "pink"
    FUCHSIA = "fuchsia"
    PURPLE = "purple"
    VIOLET = "violet"
    INDIGO = "indigo"
    BLUE = "blue"
    AZURE = ""
    CYAN = "cyan"
    JADE = "jade"
    GREEN = "green"
    LIME = "lime"
    YELLOW = "yellow"
    AMBER = "amber"
    PUMPKIN = "pumpkin"
    ORANGE = "orange"
    # TODO: add the rest

THEME_COLOR: ThemeColor = ThemeColor.AMBER

def set_theme_color(color: ThemeColor) -> None:
    global THEME_COLOR

    THEME_COLOR = color
