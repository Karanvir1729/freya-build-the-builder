"""Tests of freyalib's OpenAPI/tool layer for an API that is not the kit's POST /<name> shape: arbitrary paths,
GET with path and query parameters, operationIds as names, an identity field named after a call variable
(clientRef), $ref schemas. Also checks that the kit API still gives the old tools and that lint accepts the
new tools. No platform call.

    python3 builder/tests/test_api_general.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "builder"))
import freyalib as fl  # noqa: E402
from lint import lint  # noqa: E402

BASE = "https://card-mock.example.workers.dev/api"
API = {
    "openapi": "3.0.3",
    "servers": [{"url": BASE + "/"}],
    "paths": {
        "/api/v2/accounts/{clientRef}": {
            "get": {
                "operationId": "getAccountSummary",
                "summary": "Summary of the client account.",
                "parameters": [
                    {"name": "clientRef", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "period", "in": "query", "required": False,
                     "schema": {"type": "string", "enum": ["current", "previous"]}, "description": "Which statement."},
                ],
                "responses": {"200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Debt"}}}}},
            }
        },
        "/statement/email": {
            "post": {
                "operationId": "sendDocumentEmail",
                "requestBody": {"content": {"application/json": {"schema": {
                    "type": "object", "required": ["clientRef", "email"],
                    "properties": {"clientRef": {"type": "string"},
                                   "email": {"type": "string", "description": "The address to send the statement to."}}}}}},
                "responses": {"200": {"content": {"application/json": {"schema": {
                    "type": "object", "properties": {"ok": {"type": "boolean"}}}}}}},
            }
        },
        "/documents/summary": {
            "get": {
                "parameters": [
                    {"name": "clientRef", "in": "query", "required": True, "schema": {"type": "string"}},
                    {"name": "accountLast4", "in": "query", "required": True, "schema": {"type": "string"},
                     "description": "Last four digits of the card."},
                ],
                "responses": {"201": {"content": {"application/json": {"schema": {
                    "type": "object", "properties": {"total": {"type": "number"}}}}}}},
            }
        },
        "/kart/borç": {"get": {"operationId": "borçSorgula", "responses": {"200": {}}}},
    },
    "components": {"schemas": {"Debt": {"type": "object", "properties": {
        "totalDebt": {"type": "number", "description": "Total account summary."},
        "minimumPayment": {"type": "number"}, "currency": {"type": "string", "enum": ["TRY"]}}}}},
}


def run_hook(tool, body):
    """Run a tool's pre_process_code the way the platform does: `config` is the substituted request."""
    params = tool["function"]["parameters"]["properties"]
    config = {"url": params["url"]["default"], "method": params["method"]["default"],
              "headers": {"Content-Type": "application/json"}}
    if body is not None:
        config["body"] = dict(body)
    exec(tool.get("pre_process_code") or "", {"config": config, "vars": {}})
    return config


def test_names_and_specs():
    names = fl.tool_names(API)
    assert names == ["getAccountSummary", "sendDocumentEmail", "summary", "borcSorgula"], names
    for n in names:
        assert fl.tool_name_of(n) == n
        assert fl.tool_spec(API, n)
    s = fl.tool_spec(API, "getAccountSummary")
    assert s["method"] == "GET" and s["path"] == "/api/v2/accounts/{clientRef}", s
    assert s["path_params"]["clientRef"]["required"] is True
    assert s["query_params"]["period"]["enum"] == ["current", "previous"]
    assert s["fields"] == {} and s["has_body"] is False
    assert s["response_props"]["totalDebt"]["description"] == "Total account summary."       # $ref followed
    assert s["response_props"]["currency"]["enum"] == ["TRY"]
    # found by the last non-parameter path segment, any method
    assert fl.tool_spec(API, "accounts")["operation_id"] == "getAccountSummary"
    assert fl.tool_spec(API, "email")["method"] == "POST"
    d = fl.tool_spec(API, "summary")
    assert d["path"] == "/documents/summary" and set(d["query_params"]) == {"clientRef", "accountLast4"}
    assert d["response_props"]["total"]["type"] == "number"                                   # 201 response
    try:
        fl.tool_spec(API, "close_call")
        raise AssertionError("close_call does not exist in this API")
    except KeyError:
        pass
    assert fl.base_url(API) == BASE


def test_get_with_call_var_in_path():
    fl.CALL_VARS.add("clientRef")
    try:
        t = fl.api_tool(API, "getAccountSummary", description="Read the debt.", omit=["period"])
        p = t["function"]["parameters"]["properties"]
        assert t["function"]["name"] == "getAccountSummary"
        assert p["url"]["default"] == BASE + "/api/v2/accounts/{{clientRef}}", p["url"]
        assert p["method"]["default"] == "GET"
        assert "body" not in p, p                 # a GET without a request body sends none
        assert "pre_process_code" not in t
        # the optional query parameter, model-filled: a body leaf the hook moves into the url, body dropped
        t2 = fl.api_tool(API, "getAccountSummary")
        b = t2["function"]["parameters"]["properties"]["body"]
        assert b["properties"]["period"] == {"type": "string", "default": "{{period}}", "description": "Which statement.",
                                             "enum": ["current", "previous"]}, b
        assert b["required"] == []
        cfg = run_hook(t2, {"period": "previous"})
        assert cfg["url"] == BASE + "/api/v2/accounts/{{clientRef}}?period=previous", cfg
        assert "body" not in cfg
        cfg = run_hook(t2, {"period": ""})
        assert cfg["url"] == BASE + "/api/v2/accounts/{{clientRef}}", cfg
        # a baked query value goes straight into the url
        t3 = fl.api_tool(API, "getAccountSummary", baked={"period": "current"})
        assert t3["function"]["parameters"]["properties"]["url"]["default"] == BASE + "/api/v2/accounts/{{clientRef}}?period=current"
        try:
            fl.api_tool(API, "getAccountSummary", baked={"period": "last"})
            raise AssertionError("a baked value outside the enum must be refused")
        except ValueError:
            pass
    finally:
        fl.CALL_VARS.discard("clientRef")


def test_get_without_call_var_is_model_filled():
    # clientRef not declared as a call variable: the model fills it and the hook puts it in the path
    t = fl.api_tool(API, "getAccountSummary", omit=["period"])
    p = t["function"]["parameters"]["properties"]
    assert p["url"]["default"] == BASE + "/api/v2/accounts/{clientRef}"
    assert p["body"]["required"] == ["clientRef"]
    cfg = run_hook(t, {"clientRef": " 12 34/ü "})
    assert cfg["url"] == BASE + "/api/v2/accounts/12%2034%2F%C3%BC", cfg
    assert "body" not in cfg


def test_get_query_params():
    fl.CALL_VARS.add("clientRef")
    try:
        t = fl.api_tool(API, "summary", field_descriptions={"accountLast4": "four digits"}, pre="vars['x'] = 1\n")
        p = t["function"]["parameters"]["properties"]
        assert p["url"]["default"] == BASE + "/documents/summary?clientRef={{clientRef}}", p["url"]
        assert p["body"]["properties"] == {"accountLast4": {"type": "string", "default": "{{accountLast4}}",
                                                         "description": "four digits"}}
        assert p["body"]["required"] == ["accountLast4"]
        assert t["pre_process_code"].startswith("vars['x'] = 1\n")      # the caller's hook runs first
        cfg = run_hook(t, {"accountLast4": "4821"})
        assert cfg["url"] == BASE + "/documents/summary?clientRef={{clientRef}}&accountLast4=4821", cfg
        assert "body" not in cfg
        assert "{{" not in t["pre_process_code"].replace("{{clientRef}}", "")
        compile(t["pre_process_code"], "pre", "exec")
    finally:
        fl.CALL_VARS.discard("clientRef")


def test_post_body_with_call_var():
    fl.CALL_VARS.add("clientRef")
    try:
        t = fl.api_tool(API, "sendDocumentEmail", description="Send the statement.")
        p = t["function"]["parameters"]["properties"]
        assert p["url"]["default"] == BASE + "/statement/email"
        assert p["method"]["default"] == "POST"
        body = p["body"]
        assert body["properties"]["clientRef"] == {"type": "string", "default": "{{clientRef}}"}
        assert body["properties"]["email"]["default"] == "{{email}}"
        assert "customer_id" not in body["properties"]           # only the kit's POST /<name> tools carry it
        assert body["required"] == ["email"], body["required"]
        assert "pre_process_code" not in t
        assert fl._model_fields(t) == [("email", "email")]
    finally:
        fl.CALL_VARS.discard("clientRef")


def test_kit_unchanged():
    kit = fl.load_api(ROOT / "tools" / "openapi.json")
    assert fl.tool_names(kit) == ["verify_identity", "get_account", "create_promise", "add_note", "schedule_callback",
                                  "transfer_to_agent", "close_call"]
    for n in fl.tool_names(kit):
        t = fl.api_tool(kit, n)
        p = t["function"]["parameters"]["properties"]
        assert p["url"]["default"] == fl.base_url(kit) + "/" + n
        assert p["method"]["default"] == "POST"
        assert list(p["body"]["properties"])[0] == "customer_id"
        assert p["body"]["properties"]["customer_id"] == {"type": "string", "default": "{{customer_id}}"}
        assert "customer_id" not in p["body"]["required"]
        assert "pre_process_code" not in t
    assert fl.CALL_VARS == {"customer_id"}


def test_lint_accepts_general_tools():
    fl.CALL_VARS.add("clientRef")
    try:
        nodes = {}
        nodes["fin"] = fl.end_node("fin", "done", "Goodbye.")
        tools = [fl.api_tool(API, "getAccountSummary", description="Read the debt."),
                 fl.api_tool(API, "summary", description="Read the debt by card."),
                 fl.api_tool(API, "sendDocumentEmail", description="Send the statement.")]
        nodes["talk"] = fl.conv("talk", "Help the customer.", tools=tools,
                                transitions=[fl.ok_true("sendDocumentEmail", "fin", "sent")])
        wf = fl.assemble("talk", nodes, "You are the bank's assistant.", [])
        fl.check(wf)
        findings = lint(wf, API, call_vars=["clientRef", "now"])
        bad = [f for f in findings if f["level"] == "ERROR" and ("parameters" in f["where"] or "operation" in f["message"])]
        assert not bad, bad
        warns = [f for f in findings if "not in the spec" in f["message"] or "nothing sets" in f["message"]]
        assert not warns, warns
        # a wrong url is still caught
        tools[2]["function"]["parameters"]["properties"]["url"]["default"] = BASE + "/statement/mail"
        findings = lint(wf, API, call_vars=["clientRef", "now"])
        assert any(f["level"] == "ERROR" and f["where"].endswith("parameters.url") for f in findings)
    finally:
        fl.CALL_VARS.discard("clientRef")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print("ok", t.__name__)
    print("%d tests passed" % len(tests))
