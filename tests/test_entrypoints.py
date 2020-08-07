def test_proc_insar_isce(script_runner):
    ret = script_runner.run('hyp3_insar_isce', '-h')
    assert ret.success


def test_procAllS1StackISCE(script_runner):
    ret = script_runner.run('procAllS1StackISCE.py', '-h')
    assert ret.success


def test_procS1ISCE(script_runner):
    ret = script_runner.run('procS1ISCE.py', '-h')
    assert ret.success


def test_procS1StackISCE(script_runner):
    ret = script_runner.run('procS1StackISCE.py', '-h')
    assert ret.success
