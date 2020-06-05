# Cloning your Citrix Storefront for security awareness
One of the most important chains in your security link is going to be your end users. The reason for this is we can't control the actions of others, regardless of the number of security controls you implement, short of removing all internet access. To help make that link stronger, we'll develop a social engineering exercise to test the ability for our employees to detect clones of a common logon page they use. In this case, a Citrix Storefront portal.

## Citrix Storefront
Citrix Storefronts are one of the more common application deployment platforms that you'll see across enterprises today and chances are if your end users are using it in day in and day out they are familiar with what the page will look like and may forget to look for the warning signs of a forgery.

## Boots on the ground
Before we jump into the attacker machine setup, I wanted to provide more sustenance on the process of cloning these type of pages because there's much to learn when you read the source.

1. Root-relative vs absolute links
2. JavaScript generated elements
3. Internal vs External
4. Form method post actions
5. Attacker Machine Setup

### Root-relative vs absolute links
Most web pages include resources that are found off the web root or other third party resources in order to build the page. If you were to save the index file of your Storefront onto your local pc and try to view the page, it'll either be blank or otherwise broken because it's looking off your root for required resources. Let me show you what I mean:

I grabbed the first few lines of the index.html page from a Storefront portal. When you see links, such as src="/ or href="/, those are root-relative links. In order for your clone to work, you need to replace these links with the absolute link to the required resource. 

For example, if your base url is 'https://fake.example.com' then `href="/vpn/images/AccessGateway.ico"`should become `href="https://fake.example.com/vpn/images/AccessGateway.ico"`. There are a few occurrences of this throughout the index file, which also includes the declarations for `var Resources` and `var eula`. 

```HTML
<link rel="SHORTCUT ICON" href="/vpn/images/AccessGateway.ico" type="image/vnd.microsoft.icon">
<META http-equiv="Content-Type" content="text/html; charset=UTF-8">
<META content=noindex,nofollow,noarchive name=robots>
<link href="/vpn/js/rdx/core/css/rdx.css" rel="stylesheet" type="text/css"/>
<link href="/logon/themes/Default/css/base.css" rel="stylesheet" type="text/css" media="screen" />
<link rel="stylesheet" href="/logon/fonts/citrix-fonts.css" type="text/css">
<link href="/logon/themes/Default/css/custom.css" rel="stylesheet" type="text/css"/>
<script type="text/javascript" src="/vpn/js/rdx.js"></script>
<script type="text/javascript" src="/vpn/login.js"></script>
<script type="text/javascript" src="/vpn/js/views.js"></script>
<script type="text/javascript" src="/vpn/js/gateway_login_view.js"></script>
<script type="text/javascript" src="/vpn/js/gateway_login_form_view.js"></script> 
```

Take the time to read and go through the source code of the index page to get an understanding of what it's going to do when it's launched. If you do, you'll notice something important is missing.

### JavaScript generated elements
After you fix the root-relative links and load your page, you've probably noticed that you are missing the logon form. This is because when you load the page, it calls a js file at `/vpn/js/gateway_login_form_view.js` that builds the div elements that make up the form. This information will only exist when a JavaScript engine, such as your browser, executes the script and builds the code. 

To get past this hurdle, we're going to incorporate [https://phantomjs.org/](PhantomJS) a scriptable headless browser. Despite no longer being maintained, this is still a handy utility. What this utility will do is load the target url, including its dynamically generated content and output all the pertinent html code, including the div elements that you won't see if you download index.html manually.

Using this engine is quite simple, you build a command file for the engine, then when you call PhantomJS pointing to the instruction file and the target URL. I've included a simple script to get what we need.

```bash
tristram@kali:~$: phantomjs /path/to/build.js https://fake.example.com > index.html
```

**Build.js**
```JavaScript
var page = require('webpage').create(),
  system = require('system'), address;
address = system.args[1];
page.scrollPosition= { top: 4000, left: 0}
page.open(address, function(status) {
  if (status !== 'success') {
    console.log('** Error loading url.');
  } else {
    console.log(page.content);
  }
  phantom.exit();
});
```

### Internal vs External
When you're cloning a Storefront page, you need to be cognizant of are you cloning the `public` page or `private` page as the source code is different. This is important to keep in mind as a clone generated from the private network may not display properly if you present it from the internet and vice-versa. 

Keep in mind our goal is not necessarily functionality; we want a visual copy with a working form. Make a few changes and your page locally until you get the page to display without any errors. For example on the functionality, the public facing clone will produce errors if you do not omit the 'rdx.js' javascript from being called.

With the script referenced in this commit, it's been coded to *clone public facing sites*.

### Form method post actions
To keep this simple, we are going to use a custom php page and designate our form method action to point to the root-relative link of this page, since we're hosting this on our attacker machine. I included a very quick and simple php page in this repository. What this file will do is when a post is submitted, it's send the data to our php page, from which it'll append a log with the username, password, ip and user agent to a log file. 

**IMPORTANT** 
  * Avoid keeping the log file in the web root *(change this in line 41)*
  * www-data needs to be able to write to the log file

## Attacker Machine Setup
Now that we have a better understanding of what we're trying to accomplish, let's fire up our Kali machine and get to work.

1. Clone your target StoreFront Portal
2. Create our post.php file
3. Identify the username/password field names
4. Create log file for post.php and assign proper permissions
5. Start Apache and test

### Clone your target StoreFront Portal
I wrote a simple python script called 'storefront-cl.py' to facilitate the cloning and cleaning process, that works as of the date of posting this. It takes in two parameters, the target url and the designated path to your custom php file. Once you run the script, it will:

* Create the PhantomJS script in the current directory
* Execute the PhantomJS headless browser engine
* Write the content to index.html off the current directory
* Adjust the link references
* Run additional clean up steps

![Alt text](https://github.com/gh0x0st/storefront_cloner/blob/master/Screenshots/storefront-cl.png?raw=true "storefront-cl")

### Create our post.php file
You can utilize your own php file, or copy down the one I provided in the repository. Depending on the route you want to take, you can keep this as a credential harvester or replace that functionality with an awareness landing page for your organization. 

If you go the credential harvester route, be sure to modify the last line of the file which is a page refresh to a designated URL, to help stay under the radar, set this to the actual URL. The reason for this is the user might not get suspicious and simply try again, getting the intended content and moving along.

```HTML
<meta http-equiv="refresh" content="0; url=https://real.example.com" />
```

### Identify the username/password field names
Within our post.php file we are capturing the username and password from the POST so we can append it to a log entry. A common mistake people make is assume the input name is going to be username/password respectively, or they print out the entire POST array, which is ugly. This is where reading the source code will help us out. 

For example, using the below snippet we can see the input field for the username and password and as you see the names are not intuitive. 

```HTML
<input type="text" id="Enter user name" class="prePopulatedCredentials" autocomplete="off" spellcheck="true" name="a1825983723992608" size="30" maxlength="127" width="0" autofocus="" title="Enter user name">

<input type="password" id="passwd" class="prePopulatedCredentials" autocomplete="off" spellcheck="true" name="a7678120670087784" size="30" maxlength="127" width="0" />
```

Using the information we verified, we can test to ensure we are capturing the credentials.

```PHP
<?php
$username = $_POST["a1825983723992608"];
$password = $_POST["a7678120670087784"];
echo "Username: $username | Password: $password";
?>
```
![Alt text](https://github.com/gh0x0st/storefront_cloner/blob/master/Screenshots/post-credentials.png?raw=true "post-credentials")

### Create log file for post.php and assign proper permissions
As I mentioned previously, you should not create your log file in the web root, unless you want someone to snoop in on your results. Just make sure you give www-data permissions to write to the file itself. 

![Alt text](https://github.com/gh0x0st/storefront_cloner/blob/master/Screenshots/capture-txt.png?raw=true "capture-txt")

### Start Apache and test
Now that we have everything loaded up, browse to http://127.0.0.1, enter in some credentials and see if you can successfully log the entries to a log file. If everything works from here, then your next step is simple; engineer a solution to get your staff to connect to the site. Get creative.

![Alt text](https://github.com/gh0x0st/storefront_cloner/blob/master/Screenshots/captured-creds.png?raw=true "captured-creds")

As a security professional these exercises can be very fun and informative, especially when you craft the engagement yourself. However, it's very common to lose focus on the awareness aspect and our efforts may turn into ego boosters; avoid doing that. Just keep the following points in the back of your mind before you start to execute your exercise:

1. Don't social engineer your employees just to single them out and shame them
2. Utilize the engagement to identify gaps in your awareness program
3. When staff fail, walk them through some of the red flags that could've helped them, such as a wrong url or no SSL icon
4. Reward the people who report your campaign - these are your security heroes

Be informed, be secure.
