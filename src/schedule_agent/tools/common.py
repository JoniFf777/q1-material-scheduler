def ok(data, summary):
    return {"ok": True, "data": data, "summary": summary}


def error(code, message, retryable=False, **extra):
    return {"ok": False, "error_code": code, "message": message,
            "retryable": retryable, **extra}
