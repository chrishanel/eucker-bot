# Uecker-bot
Relaying all the scores and data you can shake a Mendoza line bat at

"I count hits, walks, fielder’s choice, everything. If I hit it good, I count it. By my own system, I batted .643." -Bob Uecker

# MLB Battlegrounds
[Design Document](https://docs.google.com/document/d/1S3uQrraa4uiAM9_QRo4JQJQQv2qH9dgt_Lg5MEOMA7Y/edit)

## Functional View

|Command   | Pseudo Logic  | 
|---|---|
|`/balance`   | READ balance  |
| `/wager` [x] [team]  | READ `outcomes` where valid<br/>READ `balances` for `users` and check if > `x`<br/>CREATE record for `wagers`<br/>UPDATE `balances`   |
|  `/results` | READ `wagers` for `users`.`id` where `outcomes`.`date` is today and display `games`.`result` |
| `/results` [week/month/season] | As above, with extra factor of `outcomes`.`week` == this week OR `outcomes`.`season` == this season |
| `/bonus` | READ `users_bonuses` where `user_id` is me and status is active |
| `/use [x]` | READ `users_bonuses` and confirm they have `x`<br/> APPLY `bonus` to appropriate outcome (balance/wagers/other players etc.) <br/> UPDATE `users_bonuses`.`status` to decrement by 1 (allowing multi-use bonuses) |
| `/games` | READ `games` where date is today |

### Problem Spaces
- How to determine timey stuff:
    - "today"
    - Determine "this week"
    - Determine "this season"
- Schedule that updates results
    - results for a given game (scheduled job?) (outcomes are resulted)
    - update balance given a result (should be part of above job... python? SQL? print and pencil?)
- Bonuses
    - Daily job to award "winner(s)" for a given day
    - Job to then look at "streaks" of wagers and/or wins
    - How to apply bonuses? Probably just need to program them - can't think of a way to abstract to database, given they vary in effects
- Balances
    - Managing this? Better to calc each time or have a table which has the current number at all times, which can be reconciled in a daily job?
- Edge cases
    - Delays? Daily job held back until "resulted"? Or plow ahead and disregard from "today"
    - Suspended?
    - Doubleheaders - cater for this using the `outcomes.


## Database Schema
```mermaid
erDiagram
    USERS ||--o{ WAGERS : places
    WAGERS }o--|| OUTCOMES : on
    OUTCOMES }o--|| GAMES : "placed on"
    USERS ||--|| BALANCE : has
    USERS ||--o{ USERS_BONUSES : gains
    USERS_BONUSES }o--|| BONUSES : "is used"
```