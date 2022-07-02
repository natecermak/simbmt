# SimBMS - Simulate Better Mass Transit

This is a python library oriented towards evaluating and (hopefully) demonstrating the benefits of user-aware bus^1 routing schemes. By user-aware, we mean that bus behavior depends on when and where the riders are, and where they wish to go.


## Notes
^1 This repo is currently bus-oriented in many of the design assumptions, but may at some point be expanded to evaluate mixed fleets (cars, vans, busses, trains, etc).

## To-do

*Naber:*

- The closest (in terms of time of arrival) bus should be assigned, not just the first in the Bus list.

*Static routing:*

- Passengers do not walk to routes in StaticRoutingOracle
- Routes do not currently pick up passengers
- Passengers need to actually PLAN near-optimal routes with the routes (not sure how to do this).

*More oracles to implement:*

- spoke, spoke-and-hub static routes
- the batched travelling salesman approach

*More performance metric ideas:*

- [X] Time to destination
- [ ] Excess time to destination (actual time - optimal time)
- [ ] Excess time ratio (actual time / optimal time)
- [ ] Typical bus occupancy (person-miles / bus-miles)
- [ ] Robustness to 'noise' (traffic/speed variation, flaky passengers, etc)


## License
Copyright 2022 Nathan Cermak.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

