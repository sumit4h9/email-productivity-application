# Fix Invalid Hook Call Error in Dashboard

## Tasks
- [x] Refactor Dashboard.tsx to use useQueries instead of calling useAccountStatus in forEach loop
- [x] Import useQueries from @tanstack/react-query and oauthAPI from @/lib/api
- [x] Replace the useEffect with forEach with a useQueries call for all account statuses
- [x] Update accountStatuses state to be derived from the useQueries results
- [x] Remove the invalid hook calls inside loops
- [x] Test the app to confirm the error is resolved
