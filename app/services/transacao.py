from contextlib import contextmanager


@contextmanager
def transacao(db):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise