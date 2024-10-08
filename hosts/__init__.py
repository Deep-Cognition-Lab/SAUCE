from __future__ import annotations
from functools import cache
from typing import Type

import hosts.host
import hosts.random
import hosts.round_robin
import hosts.mafia_host

@cache
def get_hosts()-> dict[str,Type[hosts.host.Host]]:
    return {
        hosts.round_robin.HostRoundRobin.NAME: hosts.round_robin.HostRoundRobin,
        hosts.random.HostRandom.NAME: hosts.random.HostRandom,
        hosts.mafia_host.MafiaHost.NAME: hosts.mafia_host.MafiaHost
    }

@cache
def get_host_class(name: str) -> Type[hosts.host.Host]:
    known_hosts = get_hosts()
    return known_hosts.get(name)

