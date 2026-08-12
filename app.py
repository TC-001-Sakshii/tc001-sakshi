import os

from fulfilment import create_app


app = create_app()

if _name_ == "_main_":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)