# Service

These files provide an interface for an autostart-service.

- `service/install.sh` installs the environment.  
  Assumes a git repository is there.
  Writes a cron-job for the service to start on boot.
  Installs the packages.
  You can run this several times to update the repository.
- `service/start.sh` restarts or starts the service.  
  You can use environment variables with it.
  `service/start.sh --update` runs `service/install.sh`
  before the server is started.
  If the service is already started, it is stopped.
  If it can not be stopped, this script aborts.
- `service/stop.sh` stops the service.
  If the service can not be stopped, this script aborts.
- `service.pid` contains the process ID of the service.
  `service/start.sh` creates this file when the service is started.
  `service/stop.sh`
- `service/service.log` contains the process output.  
  This file is created anew for each process.

## Install as Service

Use this to edit your crontabs:

```
crontab -e
```

Add the following to them, where `/home/pi/wer-ist-da` is the location of
the repository:

```
@restart /home/pi/wer-ist-da/service/start.sh --install  >/dev/null 2>&1
@daily /home/pi/wer-ist-da/service/start.sh --install  >/dev/null 2>&1
```

[Read more in crontab](https://www.cyberciti.biz/faq/how-do-i-add-jobs-to-cron-under-linux-or-unix-oses/).


