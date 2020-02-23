
def global_test_init():
    import os
    import stat
    from ..import set_debug

    set_debug(True)

    BASEDIR = os.path.dirname(__file__)
    IDENTITY1 = os.path.join(BASEDIR, 'data/rsa1')
    IDENTITY2 = os.path.join(BASEDIR, 'data/rsa2')
    mod_0600 = stat.S_IRUSR | stat.S_IWUSR
    os.chmod(IDENTITY1, mod_0600)
    os.chmod(IDENTITY2, mod_0600)
