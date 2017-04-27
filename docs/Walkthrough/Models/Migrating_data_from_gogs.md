# Migrating data from gogs

This is a walk through of Migrating data from gogs database into redis   
jumpscale Model and into redis using the  gogs factory and provided tools.
to migrate all the data available in the gogs sql database three simple commands are required depending on what you need.

The commands to run are:

 - To fetch the users you can use the gogs factory by running:
   ```python
   j.clients.gogs.getUsersFromPSQL()
   ```

 - To fetch the issues you can use the gogs factory by running:
   ```python
   j.clients.gogs.getIssuesFromPSQL()
   ```

 - To fetch the repos you can use the gogs factory by running:
   ```python
   j.clients.gogs.getReposFromPSQL()
   ```

 - To fetch the organizations you can use the gogs factory by running:
   ```python
   j.clients.gogs.getOrgsFromPSQL()
   ```


Now that you have the data migrated you can view  it using the issuemanager tool,
a wrapper around the model to allow searching using specific fields.

To use it run:

- To search models for all users with email `test@mail.com`, you can use the gogs factory by running:
    ```python
    collection = j.tools.issuemanager.getUserCollectionFromDB()
    collection.find(email='test@mail.com')
    ```

- To search models for issue with name `issue name`, you can use the gogs factory by running:
    ```python
    collection = j.tools.issuemanager.getIssueCollectionFromDB()
    collection.find(name='issue name')
    ```
- To search models for all repos with user `3` as member, you can use the gogs factory by running:
    ```python
    collection = j.tools.issuemanager.getRepoCollectionFromDB()
    collection.find(member=3)
    ```
- To search models for  all organizations with repo `12` in it, you can use the gogs factory by running:
    ```python
    collection = j.tools.issuemanager.getOrgCollectionFromDB()
    collection.find(repo=12)
    ```
```
!!!
title = "Migrating Data From Gogs"
date = "2017-04-08"
tags = []
```
