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
import time

from hawk import zpages
from flask import Flask, jsonify

from hawk.contrib.flask import get_blueprint
from hawk.zpages.components import ZTable, TableStyle


def create_test_zpage() -> zpages.ZPage:
    zp = zpages.ZPage(
        title="Test Page",
        description="A test ZPage",
    )

    with zp.container() as c:
        c.add(ZTable(
            cols=["Property", "Value"],
            rows=[
                ["Name", "Test Page"],
                ["Description", "A test ZPage"],
                ["Author", "Roman Hlushko"],
            ],
            style=TableStyle.PROPERTY,
        ))

    return zp


def busy_wait(duration: float) -> None:
    end_time = time.time() + duration

    while time.time() < end_time:
        time.sleep(0.1)


def create_app() -> Flask:
    app = Flask(__name__)

    # Register zpages
    zpages.add_page("test", create_test_zpage())

    # Register debug blueprint
    app.register_blueprint(get_blueprint(prefix="/debug"))

    @app.route("/")
    def welcome():
        busy_wait(1)

        return jsonify({
            "message": "Welcome to Hawk: Flask Example",
            "debug_url": "/debug/",
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
