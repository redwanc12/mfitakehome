## Problem
My understanding of this problem is to create a financial tracking and payment executing program that, using the Method Financial API to "execute" payments, will provide an easy to use yet robust system for Dunkin Donuts Employee payments.

We are dealing with a scale of about 50k payments every two weeks across 10k employees, 5 sources, and 30 branches. We need the ability to generate payment status data, branch data by batch, and source data by batch. 

Due to the nature of financial systems, this system should be quite error proof and able to deal with, or easily implement things that will deal with, things that could go wrong in a financial system. On top of that, it should have consistent data, book keeping, and an efficient system to safely and quickly retrieve up to date data.

## Frontend
For the frontend, I just created a basic react app consisting of two pages: One for submitting new reports, and one for viewing old reports(seperated by batches, with the ability go generate CSV files for each batch). 

When creating a new report, to view the XML data in a "succint" way, I've created a parser in the back end that returns aggregated data. That data is then displayed as a table that can be sorted by either branches or sources. 

I've chosen to handle the parsing in the backend to prevent the client from having to process heavy computations. Using a Python library built on C, an XML with about 50k rows can be processed and returned in under one second. 

In the future, there can also be some way to view data by individual users. This can be done through taking advantage of virtualized lists, pagination, and a "search bar" feature. Due to the structure of this system, this feature would be easy to implement into the existing codebase. However, since the question did not ask for this, I've decided to skip this feature for now. And since this is meant to be a basic demo, I've also decided to not worry about things like memory persistance, security, or production level react/javascript code.

Demo seen here:
https://youtu.be/MDe__1Vc5Sc

[![Demo](https://i.imgur.com/wNcAkAt.png)](https://youtu.be/MDe__1Vc5Sc)


## Backend
For the Backend, I've decided to create a simple REST API using Django Rest Framework. Anything would have worked, but I decided to go with DRF for no reason besides wanting to brush up on it since many of my other interviews are in Django. 


### Data
The XML file has shown that there exists a unique identifier for all sources/employees, dunkin_id (d_id). For each source/employee, the Method Financial (MFI) maintains a unique identifier using acc_id (*note: for the sake of simplicity and explaining system flow, I'm going to assume that a dunkin_id is directly related to an MFI account acc_id, ignoring the intermediate step of entity_id.*)


Since the MFI Api and our internal systems use two different unique identifiers to refer to the same object, we use two key:value stores to map them id's to each other, and fluently convert between them.


d_id_to_acc_id: {d_id: acc_id, ...}


acc_id_to_d_id: {acc_id: d_id, ...}


Since this problem doesnt require us to provide any data about employees or sources, we could get away without creating any table to represent employees or sources. All payments could be created uses just these two maps. However, this only works under the assumptions that each d_id already has a corresponding MFI acc_id. Since we have to also create the MFI accounts, we cannot make this assumption. Furthermore, payment tracker and executor systems tradtionally care a lot about being able to generate reports based on employees/sources for many purposes like bookkeeping, taxes, security, etc. Given this, I will still create tables for Employees and Sources.


### Object Models

1) Employee: (d_id, mfi_created:bool, branch, first_name, last_name, phone, email, dob, plaid, loan, metadata ..)
2) Source: (d_id, mfi_created:bool, aba_routing, account_number, name, dba, ein, metadata ..)
3) Payment: (p_id, batch_id, to: d_id, from: d_id, amt, idemp_key, status, time_created, last_updated)

The Employee and Source objects do not contain any information about "batches" or even "payment" data. This is because the same employee/source object can referenced regardless of the payment or batch. Further discussion on wallets/user-payment-relationships In the following sections.

For the Payment object, the p_id unique identifier may be seperate from the payment_id unique identifier that the MFI Api uses to identify each payment object, in which case we may need maps to convert between the payment_id's between the two systems.  For amt, I will assume that the currency is always USD, and will store the field as a string to prevent floating point errors. Status should be one of ["UNPROCESSED", "PROCESSING", "SUCCESS", "FAILED"].

### SQL vs NoSQL

The above data models can be implemented in both SQL and NoSQL databases. The decision ultimatley comes down to many factors relating to the specific needs of the system. I will not go in depth into the pro's and con's of each, since there is enough information about it online. However, for this demo application, I've decided to implement the models using a PostgreSQL database. I believe this made sense for a few reasons:
1) This is a simple demo application, and setting up a SQL database is simpler than NoSQL, and still serves the purpose of showing system flow.
2) 50k rows every two weeks is a very small and manageable workload for a SQL database. Especially if old processed payments are moved to another, read-only, database. Performance will not be a problem here.
3) SQL's ACID properties will ensures that our data will be consistent as we write and update our Payment's rows. This can be crucial for a payment tracker and executor system.

### CSV reporting

All payment objects will be added to the Payment's table with status "UNPROCESSED" at the time of batch approval, and each indivudal payment object will be updated as it move alongs the pipeline. This means generating a CSV to get payments and their status's is as simple as returning a CSV representing a query of all items in the Payment's table where batch_id=batch_id. 

To generate CSV for Sources/branches, we could simply do a query on the Payment's table specifying batch_id, and using the status/amt fields to calculate how much each source/branch has paid/received, and then return a CSV with that data. 

Another way that would be to maintain another table for aggregated data, where each entry corresponds with one batch. This would be faster for reading and generating CSV files since we don't have to recalculate, but it will also lead to more writes and having to maintain two databases. However, since there are only about 5 sources and 30 branches, the write speed should not be an issue even as we scale with increases in payments. We can update this table on the fly and have it also act as another, seperate, table that also keeps track of payments, and having two seperate records of payments can be used to check the other table to ensure no errors/inconsistencies have occured.

If we are okay with slightly delayed data, then we also don't have to write to this table on the fly. We can run a service that queries the Payment's table once every 6 hours and updates the batch data. This has the benefit of fast CSV generation (precomputation). We can also run the payment query only when the client sends a request for the CSV, and use this table as a sort of cache. This can help with having both moderately fast CSV generations and recent data. I will go with the second option (updating on the fly).



    {batch_id1:
    
        date_approved: timestamp
        
        sources: [
        
            {
            
                d_id,
                
                initial_owed,
                
                initial_owed_count,
                
                paid_so_far,
                
                paid_so_far_count,
                
                last_updated
                
            },
            
            ...
            
        ]
        
        branches: [
        
            {
            
                branch_id,
                
                initial_owed,
                
                initial_owed_count,
                
                paid_so_far,
                
                paid_so_far_count,
                
                last_updated
                
            },
            
            ...
            
        ]
    batch_id2: {...}
    }
        
        

### Wallet
We might want to keep track of how much each source/employee is owed/paid, or a wallet. This would be something that is independant of batches. One way to acquire such data is to just do a query on the payments table where we filter by all rows where the from/to columns is the source/employees's d_id. Using the "amt" and "status" columns, we can calculate how much each employee/source has been overall paid/received. This will work, but can lead to many heavy queries if done very often.

Another approach is to maintain an additonal system. Some of the benefits are as follows:
    1. Faster read data, can get employee data without querying the payments table and making calculations.
    2. Additional layer to double check payment balances are correct.
    
While some of the cons here are the increased complexity from maintaining another system, a possibility of inconsistent data, and many more writes than our previous approach. 

One way of implementing this can be to create a table for wallets that would be 1:1 with its respective employee, and this can maintain aggregated data per user. This would be a very simple system to maintain, and would very quickly be able to read and provide aggregated data per employee/source. However, this loses the ability to get a list of all payments involvng a user, which may be important down the line in generating payment histories or doing bookeeping.

To sidestep this, another solution can be to build a relationship between users and all the payments they are in. Then, we still have to calculate each payment to provide aggregated data, but we can retrieve the payments corresponding with each employee/source very quickly, while still having the option to generate a payment history list for each employee/source. In SQL, this can be done with a one to many relationship, and in NoSQL, this can be done with a wide column datastore like Cassandra.

Depending on how often we expect employee balance information to be requested, we can implement one or both of these solutions. These would be very straightforward to implement into the current code structure, but since this problem does not ask for any employee specific data, I will skip over this feature for now.

### Ledger
A debit/credit system to make sure every payment is accounted for. This can be implemented as one table with employees and sources alike. This will help double payments be caught, as well as give a place to keep track of credit/debit which will aid in tracking returns and reversed payments. The philosophy here is that the total sum of the debit and credit should equal to 0, and if it does not, that is an early flag that something has went wrong. 

Ledger object: (pk=d_id, debit, credit, last_updated?) Example:

- (eg_source_id, 300, 0) 
- (eg_employee_id, 0, 300) 

For the scope of this problem, I will not implement this.

### History
It's also important to log every action somewhere in case of errors, troubleshooting, accounting, etc.


## Flow/API endpoints
1) Get Summarized Data

POST request (XML file)

Client -> Server -> Returns summarized data (batch_id, total by branch/source)

2) Approve Payment Batch

POST request (XML file, batch_id)

Client -> Approve(xml file) -> Server -> initializes payments to payments table, initializes batch object to batch table -> Calls service that adds all "UNPROCESSED" payments to payments queue

3) Process Payment (payment queue)

    For each payment_id in payment queue:

        if to/from mfi_created == false:

            send payment_id to account queue

        else
            get to/from from payment table using payment_id

            use converter maps to convert to mfi_acc_id

            use that to create new Payment request to MFI API

            MFI response -> Update Payments table status to "PROCESSING"

4) Process Account (account queue)

    For each payment_id in account_queue:

        get to/from id from payment table using payment_id

        use employee/source table to get data of to/from using to/from id

        send request to MFI api to create entity/account

        update the mfi_acc_id fields in converter map, 
        
        set employee/source field: mfi_created = true

        send payment_id to payment queue

5) Get batches

GET request

Client -> Server -> returns list of batche_id's with some summarized data

6) Get CSV

POST request, (batch_id, type) where type can be payment, source, or branch. 

Client -> Get CSV(batch_id, source/branch) -> Server -> returns csv created from batch data table

Client -> Get CSV(batch_id, payment) -> Server -> returns csv created from payment table, filtered by batch_id.

7) Update Payment status

MFI Webhooks -> Server -> acc_id to d_id map -> updates Payment table status = "SUCCESS" -> get batch_id update batch data table.

## Points of Error
Due to the robust nature that is required of financial tracking and executing systems, there are many points of error that need to be addressed. The whole scope of these errors are beyond the scope of this problem, so I've listed just a few below + possible solutions.


1) Double Payments

Since the payment executor queue uses Payment objects from the Payment's table, which includes a idempotent key (using uuid4), we do not have to worry about the payments queue sending multiple requests to the MFI Api, which takes in an idempotent key. Sending in multiple requests from this queue to the MFI Api would thus be the same as sending in one request. Another possibility is that the client sends the same file to the server under the "approve payment" gateway. This could happen from the client pressing the "approve" batch button multiple times very quickly. However, since the batch_id is generated before the approve payment request is sent, this batch_id also acts like an idempotent key at this stage, and thus further approve requests can be ignored once the batch_id processing has began. Lastly, if someone sends in the same file twice but on seperate times (leading to seperate batch_id's), we could also keep a hash of files to make sure no duplicate files are being approved. 

Finally, as a security measure, we could also make sure all "approve batch" requests are sent using a valid batch_id, that is a batch_id that matches one generated within our internal system (using uuid4 tech), corresponds with the correct file, and has not been used/declined/timed-out by our system. 


2) Failed payments

The payments queue data should persist such that if the server crashes, the queue will still maintain the list of payment_id's to process, and will resuming processing once the server is back online. On top of the payments queue, we can add two additonal queues: a "rety queue" to retry payments that failed the first time, and a "dead letter queue" that stores payments that repeatidly fail. Then, then payments in the dead leter queue can be individually inspected. 


If there is an error with the payments queue: we can do a routine inspection of the payments table. For example, our system can check the day after the payment batch was initialized to make sure that no payments still have a status of "UNPROCESSED", and if they do, we can add them back into the payments queue.


If there is an error when first processing / approving the XML file: Since our code writes all Payment objects into the Payment's table in one batch add, we don't have to worry about partial file processing. **Either all Payment's from the XML get added to the table, or none do.** It should be easy to detect that no payments have been added to the payments table by generating the payments CSV associated that batch, in which case the user could resubmit it. We could also add another queue/retry/dead_letter_queue system for just processing the XML file. This would additionally give us the ability to return a response to the client without having to wait for the file to finish processing. However, since it generally takes under one minute to process the file, and because there are no users of this service except Dunkin Donuts (1 file per 2 weeks), this is most likely unnecessary.


3) Unsynced Data

If we are writing to both the Payment's table and batch data table on the fly, but somehow the data does not add up to be the same, then we know there is an error somewhere. We can use the Payment's table to "correct" the batch data table, but we should first investigate which table actually has the error. There can be a nightly system health check to make sure these are aligned, and it can raised flags or auto update to match the Payment's table, depending on how the system is designed. 


There are many ways to improve both performance, robustness, and security using basic scale concepts like sharding, multiple workers, load balancing, data duplication, etc. Most of this can be handeled automatically by a service like AWS. 

There is also an additonal account of data that is stored in the MFI databases, that can be accessed using the MFI Api. This can help us correct internal errors. 


## Conclusion

Overall I've decided to spend more time thinking about the system design than worrying about the details of any specific API. As a result, the code is not meant to reflect production level code or best practices. However, I really did enjoy thinking about and exploring the robustness of payment systems. 

As a concluding note, I realized after designing all of this that much of what I did may have already been done by the MFI Api, and I may have reinvented the wheel in my "data tracking" pursuit. In that case, I may have misunderstood the assignment. But instead of going through the MFI docs and learning exactly what I was and wasn't supposed to do, I've settled on just finishing what I have and treating the MFI Api as a sort of "black box" where I don't actually implement any interactions with it, but rather explain how my system would interact with it, as I feel that does an ample job at demonstrating how I approach and think about problems. Let me know if you guys have any questions!
