# dude
Dude will remember stuff for you, because a dude in need is a dude indeed!

Being on a laptop for 1.2/3 time of your life, you come across a lot of transient info that you may want to recall later,
your passive response to that is you store such info in a notepad and never save it because why should you have more files
on the already mucky desktop.

Here's a dude who doesn't do what some dudes do, but will do a real dude's do. (you can ignore this, it was a lame shot at being a dude)

#### dude does
dude is a command line and slack-commands tool that stores tagged textual (only ascii for now) information - called secret -
for you that can be later retrieved using tags.

##### storage
When you store a secret and give a tag (multi-word supported), the tags are broken into individual words and stemmed - taken from nltk.
These words - called keys - are associated with the secret, and the association is scored based on the number of words found in the tag.
For now, the scores are immaterial since the scoring algo is a senseless logic used as a placeholder for a more sophisticated scoring algorithm.


##### retrieval
Secrets could be retrieved back by providing any of the keys resulted in storage process.
The result also has a score associated with each score.

#### Setup

Suggest you use a virtual-environment, but its a suggestion, do what you want.
So once you've done what you want source the setup shell-script file like so:

```shell
$ source setup.sh
```

It does the following:
1. installs required python packages
2. sets some environment variables - feel free to fiddle with them
3. copies a sqlite3 db from a template (oh and deletes the template)

#### Sample shell usage

```shell
# ask dude to keep a secret
$ ./shell_dude --keep=foo bar
Secret kept! You may retrieve it using following keys: foo

# ask dude to tell you secret associated with a tag (key) (the number before the result is a score - explained later)
$ ./shell_dude foo
1.00  bar


# dude can also associate multi-word tags
$ ./shell_dude --keep="atif number" "atif - 9819638025"
Secret kept! You may retrieve it using following keys: number, atif, atif number

$ ./shell_dude --keep="someone else's number" "someone else - 9860283727"
Secret kept! You may retrieve it using following keys: someone else's number, number, els

# you get to retrieve secrets with any of the resulting keys ( :smiling_imp: )
$ ./shell_dude number
0.33  atif - 9819638025
0.33  someone else - 9860283727
```

You might want to give execute right on shell_dude, though I have done that already - wait.. never mind.

#### Sample Slack usage
Coming soon! (Procrastinating)

#### Parting note
It was a weekend project,
you may find things breakin.
dude only intends to help you,
so dont be hatin.

Peace!