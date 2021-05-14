# Meetings notes

## Meeting 1.
* **DATE: 12.2.2021**
* **ASSISTANTS: Iván Sánchez Milara**

### Minutes
*Summary of what was discussed during the meeting*
- Going through the RESTful API introduction and the basic idea of our project; idea is good, but do not think about the final application, focus on the API itself
- Do not worry much about authentication for registered users
- Discussion about the next deadline, i.e., how to implement database, especially the role of tag; almost all information for database in section "main concepts"

### Action points
*List here the actions points discussed with assistants*
- Define 'tag' concept into the wiki text with more detail
- Explain how the application would use the API in the use cases (one sentence)
- Put snippet of code that shows the use of hypermedia in example APIs
- Add example of actual clients using the Related Work APIs

### Comments from staff
*ONLY USED BY COURSE STAFF: Additional comments from the course staff*

## Meeting 2.
* **DATE: 26.2.2021**
* **ASSISTANTS: Iván Sánchez Milara**

### Minutes
*Summary of what was discussed during the meeting*
- Explaining the structure of our database
- Assistant suggsted that a binary value could have been used for Tag's meaning
  - We used string in order to make the tagging more expandable; users could create their own tags
- Discussing where, e.g., email format checking will be done
- Going through the model implementation
- Going through the database tests. Our tests seemed good
- Reminding that authentication is not necessary, and we should add it last if there is time
- Discussed our implementation ideas for Deadline 3
  - Pay most attention to resources and relations planning

### Action points
*List here the actions points discussed with assistants*
- Adding printed text to database tests as cues of what is being tested 
  - This was not required in the wiki guidelines, but it is still a beneficial practice

### Comments from staff
*ONLY USED BY COURSE STAFF: Additional comments from the course staff*

## Meeting 3.
* **DATE: 22.3.2021**
* **ASSISTANTS: Iván Sánchez Milara**

### Minutes
*Summary of what was discussed during the meeting*
- Going through our API design
- Discussed our problem related to adding Tags
  - Assistant said he will try to come up with a solution and email it to us
- Going through our Apiary. Everything seemed correct
- Assistant noted that we have a lot of resources and only 2 people, so not all of them have to be implemented
- Assistant noted that code should be reused as much as possible in the API implementation (from exercise 3)

### Action points
*List here the actions points discussed with assistants*
- If assistant comes up with a solution to the Tag problem, use it; otherwise leave as is
- Explain the Tag problem in the wiki
- Add example to the Addressability and Uniform Interface sections
- Change review_id to review URL in Tag's Apiary documentation
- Implement the most important resources first and test them (review + album resources), then move on to others

### Comments from staff
*ONLY USED BY COURSE STAFF: Additional comments from the course staff*

## Meeting 4.
* **DATE: 15.4.2021**
* **ASSISTANTS: Iván Sánchez Milara**

### Minutes
*Summary of what was discussed during the meeting*
- Going through our wiki and code
- Showing that our tests run correctly 
  - Tests were good and it was easy to see what they do 
- Checking the coverage of the tests
- We can keep the tag out of the implementation
  - Assistant will still think solutions to the problem and send an email
- Code documentation seemed good
- Assistant explained why Jinja can't be used for the client
- Assistant showed us Flask.login for possible API authentication

### Action points
*List here the actions points discussed with assistants*
- Change the 204 into 201 in PUT requests

### Comments from staff
*ONLY USED BY COURSE STAFF: Additional comments from the course staff*

## Midterm meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*


### Comments from staff
*ONLY USED BY COURSE STAFF: Additional comments from the course staff*

## Final meeting
* **DATE: 14.5.2021**
* **ASSISTANTS: Iván Sánchez Milara**

### Minutes
*Summary of what was discussed during the meeting*
- Focus was on our client since everything else was already shown to work
- Assistant noted that the actual URL for the client should have been shown in the README
- Assistant noted that we shouldn't have hardcoded the values of, e.g., the add album field
  - Otherwise everything in the client was good
- We explained our clients logo
- We provided our thoughts and feedback about this course
- Assistant was glad that we had notices a mistake in the Wiki page for DL. 5

### Action points
*List here the actions points discussed with assistants*
- None

### Comments from staff
*ONLY USED BY COURSE STAFF: Additional comments from the course staff*

