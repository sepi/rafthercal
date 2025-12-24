def config_find_server(config, server_id):
    return next(filter(lambda s: s['id'] == server_id,
                       config.CALDAV_SERVERS))


def config_expand(config):
    "Add server config to each calendar and todo config."
    for calendar in config.CALDAV_CALENDARS:
        server_id = calendar['server']
        server = config_find_server(config, server_id)
        calendar['url'] = server['url']
        calendar['username'] = server['username']
        calendar['password'] = server['password']
    for todo in config.CALDAV_TODOS:
        server_id = todo['server']
        server = config_find_server(config, server_id)
        todo['url'] = server['url']
        todo['username'] = server['username']
        todo['password'] = server['password']
