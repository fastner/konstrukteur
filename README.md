# Konstrukteur
*A static website generator*

## Getting started

### Setup

**Please install python3 and virtualenv first**

Set up a virtualenv environment and activate it

    ~$ virtualenv -p /usr/bin/python3 webdev
    ...
    ~$ . webdev/bin/activate

Install konstrukteur via pip

    (webdev):~$ pip install konstrukteur
    
Now everything is set up in your development environment.

### Create website from skeleton

To create a new website let Konstrukteur do the hard work

    (webdev):~$ konstrukteur create --name mynewweb

Konstrukteur now has created a new website project called *mynewweb*.

### Build website

The default skeleton includes a very simple theme and a web page in english and german.
Build your web site into output directory

    (webdev):~$ cd mynewweb
    (webdev):~/mynewweb$ konstrukteur

### Result

The generated web site is now located at *~/mynewweb/output*. You can copy this directory to your web server.