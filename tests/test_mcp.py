"""Local MCP server: JSON-RPC handshake, tools, clean stdout, progress notifications."""
import json
import os
import subprocess
import sys

import pytest


class Client:
    def __init__(self, tmp_path):
        env = dict(os.environ, SAWSIM_RUNS_DIR=str(tmp_path / 'runs'), SAWSIM_MATERIALS_DIR=str(tmp_path / 'mats'))
        self.p = subprocess.Popen([sys.executable, '-m', 'sawsim.cli', 'mcp'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
        self.next_id, self.notifications = 0, []

    def send(self, method, params=None, notify=False):
        msg = dict(jsonrpc='2.0', method=method, params=params or {})
        if not notify:
            self.next_id += 1
            msg['id'] = self.next_id
        self.p.stdin.write(json.dumps(msg) + '\n')
        self.p.stdin.flush()
        if notify:
            return None
        while True:
            line = self.p.stdout.readline()
            assert line, 'server closed stdout'
            reply = json.loads(line)          # every stdout line must be JSON-RPC
            assert reply['jsonrpc'] == '2.0'
            if 'id' not in reply:
                self.notifications.append(reply)
                continue
            assert reply['id'] == self.next_id
            return reply

    def call(self, name, arguments, token=None):
        params = dict(name=name, arguments=arguments)
        if token is not None:
            params['_meta'] = dict(progressToken=token)
        return self.send('tools/call', params)['result']

    def close(self):
        self.p.stdin.close()
        assert self.p.wait(timeout=30) == 0


@pytest.fixture
def client(tmp_path):
    c = Client(tmp_path)
    yield c
    c.close()


def test_handshake_and_tools(client):
    r = client.send('initialize', dict(protocolVersion='2025-03-26', capabilities={},
                                       clientInfo=dict(name='pytest', version='0')))['result']
    assert r['protocolVersion'] == '2025-03-26' and r['serverInfo']['name'] == 'sawsim' and 'tools' in r['capabilities']
    assert 'locate_resonance' in r['instructions']
    client.send('notifications/initialized', notify=True)
    assert client.send('ping')['result'] == {}
    tools = {t['name']: t for t in client.send('tools/list')['result']['tools']}
    assert {'get_guide', 'list_templates', 'describe_template', 'list_materials', 'create_material',
            'validate_config', 'run_sweep', 'locate_resonance', 'check_convergence', 'scan_parameter',
            'summarize_result', 'plot_curves', 'compare_with_reference'} <= set(tools)
    cfg = tools['validate_config']['inputSchema']['properties']['config']
    assert 'sp_stack' in cfg['properties']['model_id']['enum'] and 'material_snapshots' not in cfg['properties']
    assert client.send('nope/method')['error']['code'] == -32601


def test_unknown_protocol_version_gets_latest(client):
    r = client.send('initialize', dict(protocolVersion='1999-01-01', capabilities={}))['result']
    assert r['protocolVersion'] == '2025-06-18'


def test_tools_validate_run_plot(client, tmp_path):
    client.send('initialize', dict(protocolVersion='2025-06-18', capabilities={}))
    bad = client.call('validate_config', dict(config=dict(model_id='sp_tcsaw', mode_extension=1)))
    assert bad['isError'] and bad['structuredContent']['allowed']['mode_extensions'] == [0]
    guide = client.call('get_guide', {})
    assert 'locate' in guide['structuredContent']['guide']
    cfg = dict(model_id='sp_single_layer', points=21, start_ghz=1.7, stop_ghz=1.95)
    run = client.call('run_sweep', dict(config=cfg), token='t1')
    s = run['structuredContent']
    assert not run['isError'] and 1.78 < s['fr_ghz'] < 1.83 and s['fa_ghz'] > s['fr_ghz']
    assert any(n['method'] == 'notifications/progress' and n['params']['progressToken'] == 't1'
               for n in client.notifications)
    plot = client.call('plot_curves', dict(inputs=[s['output_dir']], output=str(tmp_path / 'p.png')))
    kinds = [c['type'] for c in plot['content']]
    assert not plot['isError'] and kinds == ['text', 'image'] and plot['content'][1]['mimeType'] == 'image/png'
    missing = client.call('summarize_result', {})
    assert missing['isError'] and 'missing argument' in missing['structuredContent']['error']
    unknown = client.call('no_such_tool', {})
    assert unknown['isError']


def test_print_config():
    for kind in ('claude-code', 'claude-desktop', 'codex'):
        p = subprocess.run([sys.executable, '-m', 'sawsim.cli', 'mcp', '--print-config', kind],
                           capture_output=True, text=True)
        assert p.returncode == 0 and 'mcp' in p.stdout
