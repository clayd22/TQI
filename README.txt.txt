README.txt


Language Choice:
        Given the amount of byte processing this parser requires, my initial thought was to implement it in C in order to run fast boolean and shifting logic.  
However, although this method would have likely parsed faster, I would not have had the helpful type checking of Typescript or Python.   
I then eliminated Typescript from my choices as it does not have the same thorough byte manipulation imports as Python.  
Given enough time to create a thorough type checking system, I would have looked to C for this task.


Function Description: 
        Our data input consists of roughly 11 billion bytes and our average message length is around 40 bytes.  This means that we need to parse approx 275 million 
individual NASDAQ messages.  Fortunately, only a small fraction of these impact our VWAP.  Thus, in order to maximize our functions efficiency, we are going to 
“fail fast” when our VWAP is not impacted by a message.  This means that we will read through the entirety of the message and avoid any computes.  
Once we have found the 9:30 start, we begin checking messages for our buy or sell signals.  To save space complexity, we do not keep track of a history of trades, 
but rather a running dictionary that holds the VWAP numerator and denominator.  Once we have reached a new hour, we add the VWAP to our return text for each stock.


Potential Improvements:
        This function parses 11gb of unzipped data in roughly 4 minutes.  Aside from a change in language, this could potentially be decreased by using a “bottom-up” 
parsing method.  This would require some knowledge of the structure of message sequences in order to predict the next message.  We could also introduce a pointer that 
could shift right logically (srli in assembly) in order to remove the likely slow .read() in python.  Ideally, this could be combined with a python wrapper and included 
in our existing framework.  Another option would be to parallelize the parsing using a python import and splitting the input file, but as this depends on hardware specs I 
did not implement it here.