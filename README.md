# Av-app

Av-app - an app that monitors Avanti clusters, services, namespaces, and tasks



## Getting Started

1. To start download the app via the .spl file, or pulling it from the repo. Eventually, this will go on Splunkbase and you can download it there.

2. Go to Settings > Data Inputs. At this point, please make sure the Avanti server you want to monitor is running

3. Under Local inputs, click on the Avanti modular input option. There you can create a new input by clicking on the "New" button.

4. Input the REST input name, which will become the source name of your data, as well as the endpoint of the avanti server you would like to montior. Then, click on "More settings" and set sourcetype to manual and use "cluster_log_2" as the type. Then for the index use avanti (for now - the searches require the avanti index for now, but this will change).
Note: Also for interval if you leave it blank the input will only run once.

5. Click "Next>", and your data will start being onboarded into splunk.

6. Go to the av-app, and you will be prompted to login via Auth0. You can not log in, but if you don't you will not be able to look at visualizations - only the clusters. Once you login, you should have access to all dashboards.

## Prerequisites

* Have Splunk Enterprise downloaded
* Have an Avanti server running
* Be a registered user under the Auth0 avanti-cli account
