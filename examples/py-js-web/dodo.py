# this uses the doitoml-dodo-pyproject loader
def task_hello():
    return dict(
        actions=[lambda: print("hello world")]
    )
