import json
import os
from random import randint

from bottle import route, run, request

from src import dude

_SERVER_HOST = os.environ['DUDE_SLACK_HOST']
_SERVER_PORT = os.environ['DUDE_SLACK_PORT']


@route('/verification', method="POST")
def verification():
    req = json.loads(request.body.read().decode("utf-8"))
    return req['challenge']


@route('/dude/command', method="POST")
def keep():
    # token=XXX&team_id=XXX&team_domain=XXX&channel_id=XXX&channel_name=directmessage&user_id=XXX&user_name=XXX
    # &command=%2Fkeep&text=foo+bar&response_url=XXX
    token = request.forms.get("token")
    channel_id = request.forms.get("channel_id")
    channel_name = request.forms.get("channel_name")
    user_id = request.forms.get("user_id")
    user_name = request.forms.get("user_name")
    command = request.forms.get("command")
    text = request.forms.get("text")
    response_url = request.forms.get("response_url")

    handler_func = eval("_%s" % command.replace("/", ""))
    res = handler_func(channel_id, channel_name, user_id, user_name, command, text, response_url)
    return res


_sarcasm = (":expressionless: let's be good to each other.", ":disappointed: quit playin!",
            ":confused: should i lol or roflmao?", ":thought_balloon: use intuition. its free.",
            "lets try that again, shall we? :metal: ", "I don't think it means what you think it means. :smirk_cat:",)

_error_msg = "Eeks! I am still new, so expect a little hiccups. Ask atif to fix the following.."


def _keep(channel_id, channel_name, user_id, user_name, command, text, response_url):
    print(text)
    tag, *secret = text.split(" ", 1)
    if tag == '' or not secret:
        res = "\n".join([_sarcasm[randint(0, len(_sarcasm) - 1)], "Hint: /keep <tag> <secret>"])
    else:
        try:
            dude.keep(secret[0], tag)
            res = "\n".join(["Kept! To recall just holla..", "Hint: /tell %s" % tag])
        except Exception as e:
            res = "\n".join([_error_msg, str(e)])
    return res


def _tell(channel_id, channel_name, user_id, user_name, command, text, response_url):
    tag, *secret = text.split(" ", 1)
    if tag:
        try:
            secrets = dude.tell(tag)
            if len(secrets) > 1:
                res = "\n".join(["Found more than one. Sorting by match strength..", ] + [s[2] for s in secrets])
            elif len(secrets) == 0:
                res = "nothing associated with %s" % tag
            else:
                res = str(secrets[0][2])
        except Exception as e:
            res = "\n".join([_error_msg, str(e)])
    else:
        res = "\n".join(["I am gonna need a tag %s! I am no God!" % user_name, "Hint: /tell <tag>"])
    return res


def _list(channel_id, channel_name, user_id, user_name, command, text, response_url):
    try:
        keys = dude.list_absolute_keys()
        if keys:
            res = "\n".join(["Found these..", ] + keys)
        else:
            res = "Tell me few secrets first."
    except Exception as e:
        res = "\n".join([_error_msg, str(e)])
    return res


run(host=_SERVER_HOST, port=int(_SERVER_PORT))
