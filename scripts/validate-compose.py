"""Read rendered Compose on stdin, emit booleans/errors only, never config values."""
import json
import sys


def validate(config):
    services = config['services']
    for service in services.values():
        for port in service.get('ports', []):
            assert port.get('host_ip') == '127.0.0.1', 'non_loopback_port'
            assert str(port.get('target')) in ('6080', '9119'), 'unexpected_port'
        for volume in service.get('volumes', []):
            assert 'docker.sock' not in volume.get('source', ''), 'docker_socket_mount'
    agent = services['hermes-sandbox']
    proxy = services['kis-proxy']
    assert not agent.get('secrets'), 'agent_has_secrets'
    assert not any(key.startswith('KIS_') for key in agent.get('environment', {})), 'agent_has_kis_environment'
    assert not proxy.get('ports'), 'proxy_published'
    assert proxy.get('read_only'), 'proxy_root_writable'
    assert all(item['type'] == 'volume' and item['target'] == '/state'
               for item in proxy.get('volumes', [])), 'proxy_unexpected_mount'
    assert {item['source'] for item in proxy['secrets']} == {'kis_env'}, 'proxy_secret_contract'
    secret_path = config['secrets']['kis_env']['file'].replace('\\', '/')
    for volume in agent['volumes']:
        source = volume.get('source', '').replace('\\', '/')
        if volume['type'] == 'bind':
            assert not secret_path.startswith(source.rstrip('/') + '/'), 'secret_inside_agent_mount'
        if volume['target'] == '/workspace/trading-agent':
            assert volume.get('read_only'), 'agent_code_writable'


if __name__ == '__main__':
    try:
        validate(json.load(sys.stdin))
    except Exception:
        raise SystemExit('compose_security_contract_failed') from None
    print('compose security contract passed')
