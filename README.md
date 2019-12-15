# analyze-data
Ad-hoc riff data analysis.

May be using node or python.

Currently there is code to retrieve the utterances from a riffdata Mongo database
and calculate the duration of all utterances, get the counts of the utterances
in various buckets and create a plot (well 3 plots) of those counts.

This was done using the Next Canada course data backup:
`mongodb_riff-test.edu.nexted.backup-20191118110847.gz`

## Setup

### Prerequisites

#### OS support
I've run this with python 3.8 installed on my kubuntu 18.04 VM with the [deadsnakes ppa][ubuntu-python-install]
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
```

I also installed the `matplotlib` OS packages:
```
sudo apt install python3-matplotlib
```

You will also need `docker` and `docker-compose` to use the scripts that start and stop a
Mongo database and the script that restores a backup to that database.

#### Initialize the repo
Then initialize the repo with a 3.8 virtual environment
```
make init VER=3.8
```

### Restore the database

Put the backup file in the `riffdata` subdirectory

Start the Docker Mongo database (this will likely have port conflicts if you've got a local
Mongo database running)
```
make up
```

Restore the backup:
```
bin/mongo-restore.sh mongodb_riff-test.edu.nexted.backup-20191118110847.gz
```

## Run

Activate the python virtual environment and then start the mongo database w/ the
data to be analyzed and then run:

```
make up
. activate
make run
```

## Clean up after working

Deactivate the python virtual environment and stop the mongo database
```
deactivate
make down
```

[ubuntu-python-install]: <https://linuxize.com/post/how-to-install-python-3-7-on-ubuntu-18-04/>
