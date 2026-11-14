// Real API responses from the demo case (seed 7, players Alex, Blake, Casey, Drew),
// used by /dev/kit to show every component in every state. Not used by the game.

import type { Clue, HostOut, MeOut, RevealOut } from "./types";

export const me: MeOut = {
  "case_id": "demo7kit",
  "title": "The Lake House Weekend",
  "intro": "Five college friends rented a cabin on Lake Wendell for their first reunion in years. Saturday night was supposed to be easy: grill, cards, too much rosé. By Sunday morning nobody would admit to anything.\n\nThe owner's prized 1970s record player was found smashed in the Sunroom. The downstairs clock stopped when it fell: 7:00 PM. Whoever was in the Sunroom at 7:00 PM broke it.",
  "demo": true,
  "day": 2,
  "days_total": 3,
  "phase": "play",
  "next_unlock_at": "2026-11-15T12:44:22.580067+00:00",
  "suspects": [
    {
      "id": 0,
      "name": "Priya",
      "role": "The doctor on call all weekend"
    },
    {
      "id": 1,
      "name": "Jordan",
      "role": "The ex-roommate who never grew up"
    },
    {
      "id": 2,
      "name": "Leo",
      "role": "The guy who brought his guitar"
    },
    {
      "id": 3,
      "name": "Maya",
      "role": "The planner who booked the cabin"
    },
    {
      "id": 4,
      "name": "Sam",
      "role": "The newcomer, someone's plus-one"
    }
  ],
  "labels": {
    "room": [
      "Porch",
      "Kitchen",
      "Boathouse",
      "Loft",
      "Sunroom"
    ],
    "time": [
      "7:00 PM",
      "7:30 PM",
      "8:00 PM",
      "8:30 PM",
      "9:00 PM"
    ],
    "item": [
      "a bottle of rosé",
      "a flashlight",
      "a fishing rod",
      "a guitar",
      "a deck of cards"
    ]
  },
  "me": {
    "idx": 0,
    "name": "Alex"
  },
  "my_clues": [
    {
      "id": "d1p0",
      "day": 1,
      "text": "Jordan was not seen at 7:00 PM.",
      "story": "Caption on a blurry group-chat photo: Jordan was not seen at 7:00 PM.",
      "format": "Photo caption",
      "fact": {
        "kind": "not",
        "a": "time",
        "s": 1,
        "v": 0
      },
      "from": "Alex"
    },
    {
      "id": "d2p0",
      "day": 2,
      "text": "Leo was seen at either 7:30 PM or 9:00 PM.",
      "story": "Handwritten on the back of a gas-station receipt: Leo was seen at either 7:30 PM or 9:00 PM.",
      "format": "Receipt note",
      "fact": {
        "kind": "either",
        "a": "time",
        "s": 2,
        "v": 1,
        "v2": 4
      },
      "from": "Alex"
    }
  ],
  "shared_clues": [],
  "board": [
    {
      "author": "Blake",
      "text": "Mine says Jordan was not seen at 7. Crossing him off.",
      "ts": "2026-11-14T12:44:24.550203+00:00"
    }
  ],
  "players": [
    {
      "idx": 0,
      "name": "Alex",
      "joined": true,
      "opened_today": true,
      "voted": false
    },
    {
      "idx": 1,
      "name": "Blake",
      "joined": true,
      "opened_today": false,
      "voted": false
    },
    {
      "idx": 2,
      "name": "Casey",
      "joined": true,
      "opened_today": false,
      "voted": false
    },
    {
      "idx": 3,
      "name": "Drew",
      "joined": true,
      "opened_today": false,
      "voted": false
    }
  ],
  "my_vote": null
};

export const host: HostOut = {
  "case_id": "demo7kit",
  "title": "The Lake House Weekend",
  "intro": "Five college friends rented a cabin on Lake Wendell for their first reunion in years. Saturday night was supposed to be easy: grill, cards, too much rosé. By Sunday morning nobody would admit to anything.\n\nThe owner's prized 1970s record player was found smashed in the Sunroom. The downstairs clock stopped when it fell: 7:00 PM. Whoever was in the Sunroom at 7:00 PM broke it.",
  "demo": true,
  "day": 2,
  "days_total": 3,
  "phase": "play",
  "next_unlock_at": "2026-11-15T12:44:22.580067+00:00",
  "suspects": [
    {
      "id": 0,
      "name": "Priya",
      "role": "The doctor on call all weekend"
    },
    {
      "id": 1,
      "name": "Jordan",
      "role": "The ex-roommate who never grew up"
    },
    {
      "id": 2,
      "name": "Leo",
      "role": "The guy who brought his guitar"
    },
    {
      "id": 3,
      "name": "Maya",
      "role": "The planner who booked the cabin"
    },
    {
      "id": 4,
      "name": "Sam",
      "role": "The newcomer, someone's plus-one"
    }
  ],
  "labels": {
    "room": [
      "Porch",
      "Kitchen",
      "Boathouse",
      "Loft",
      "Sunroom"
    ],
    "time": [
      "7:00 PM",
      "7:30 PM",
      "8:00 PM",
      "8:30 PM",
      "9:00 PM"
    ],
    "item": [
      "a bottle of rosé",
      "a flashlight",
      "a fishing rod",
      "a guitar",
      "a deck of cards"
    ]
  },
  "players": [
    {
      "idx": 0,
      "name": "Alex",
      "joined": true,
      "opened_today": true,
      "voted": false,
      "token": "5F6QRc8TyqMS",
      "url": "http://localhost:3000/play/demo7kit?token=5F6QRc8TyqMS"
    },
    {
      "idx": 1,
      "name": "Blake",
      "joined": true,
      "opened_today": false,
      "voted": false,
      "token": "_SjZ1HZftJSX",
      "url": "http://localhost:3000/play/demo7kit?token=_SjZ1HZftJSX"
    },
    {
      "idx": 2,
      "name": "Casey",
      "joined": true,
      "opened_today": false,
      "voted": false,
      "token": "L_XHk_9Rx8kI",
      "url": "http://localhost:3000/play/demo7kit?token=L_XHk_9Rx8kI"
    },
    {
      "idx": 3,
      "name": "Drew",
      "joined": false,
      "opened_today": false,
      "voted": false,
      "token": "tdPZGcFr2sHh",
      "url": "http://localhost:3000/play/demo7kit?token=tdPZGcFr2sHh"
    }
  ],
  "votes_count": 0
};

export const reveal: RevealOut = {
  "case_id": "demo7kit",
  "title": "The Lake House Weekend",
  "intro": "Five college friends rented a cabin on Lake Wendell for their first reunion in years. Saturday night was supposed to be easy: grill, cards, too much rosé. By Sunday morning nobody would admit to anything.\n\nThe owner's prized 1970s record player was found smashed in the Sunroom. The downstairs clock stopped when it fell: 7:00 PM. Whoever was in the Sunroom at 7:00 PM broke it.",
  "culprit": {
    "id": 0,
    "name": "Priya",
    "role": "The doctor on call all weekend"
  },
  "truth": [
    {
      "suspect": "Priya",
      "room": "Sunroom",
      "time": "7:00 PM",
      "item": "a guitar"
    },
    {
      "suspect": "Jordan",
      "room": "Porch",
      "time": "7:30 PM",
      "item": "a flashlight"
    },
    {
      "suspect": "Leo",
      "room": "Loft",
      "time": "9:00 PM",
      "item": "a fishing rod"
    },
    {
      "suspect": "Maya",
      "room": "Boathouse",
      "time": "8:00 PM",
      "item": "a bottle of rosé"
    },
    {
      "suspect": "Sam",
      "room": "Kitchen",
      "time": "8:30 PM",
      "item": "a deck of cards"
    }
  ],
  "chain": [
    {
      "clue_id": "d1p0",
      "day": 1,
      "player": 0,
      "text": "Jordan was not seen at 7:00 PM.",
      "eliminated": [
        "Jordan"
      ],
      "remaining": [
        "Priya",
        "Leo",
        "Maya",
        "Sam"
      ],
      "worlds_left": 276480,
      "from": "Alex"
    },
    {
      "clue_id": "d1p1",
      "day": 1,
      "player": 1,
      "text": "The person with a deck of cards was not seen at 7:00 PM.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Leo",
        "Maya",
        "Sam"
      ],
      "worlds_left": 221184,
      "from": "Blake"
    },
    {
      "clue_id": "d1p2",
      "day": 1,
      "player": 2,
      "text": "Sam had either a flashlight or a deck of cards.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Leo",
        "Maya",
        "Sam"
      ],
      "worlds_left": 86400,
      "from": "Casey"
    },
    {
      "clue_id": "d1p3",
      "day": 1,
      "player": 3,
      "text": "Jordan had either a flashlight or a deck of cards.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Leo",
        "Maya",
        "Sam"
      ],
      "worlds_left": 24192,
      "from": "Drew"
    },
    {
      "clue_id": "d2p0",
      "day": 2,
      "player": 0,
      "text": "Leo was seen at either 7:30 PM or 9:00 PM.",
      "eliminated": [
        "Leo"
      ],
      "remaining": [
        "Priya",
        "Maya",
        "Sam"
      ],
      "worlds_left": 8640,
      "from": "Alex"
    },
    {
      "clue_id": "d2p1",
      "day": 2,
      "player": 1,
      "text": "The person in the Loft had a fishing rod.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Maya",
        "Sam"
      ],
      "worlds_left": 1584,
      "from": "Blake"
    },
    {
      "clue_id": "d2p2",
      "day": 2,
      "player": 2,
      "text": "Leo was not in the Kitchen.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Maya",
        "Sam"
      ],
      "worlds_left": 1296,
      "from": "Casey"
    },
    {
      "clue_id": "d2p3",
      "day": 2,
      "player": 3,
      "text": "Priya was not in the Loft.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Maya",
        "Sam"
      ],
      "worlds_left": 1008,
      "from": "Drew"
    },
    {
      "clue_id": "d3p0",
      "day": 3,
      "player": 0,
      "text": "Jordan had either a flashlight or a fishing rod.",
      "eliminated": [
        "Sam"
      ],
      "remaining": [
        "Priya",
        "Maya"
      ],
      "worlds_left": 384,
      "from": "Alex"
    },
    {
      "clue_id": "d3p1",
      "day": 3,
      "player": 1,
      "text": "The person in the Sunroom was seen earlier than Jordan.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Maya"
      ],
      "worlds_left": 384,
      "from": "Blake"
    },
    {
      "clue_id": "d3p2",
      "day": 3,
      "player": 2,
      "text": "The person on the Porch was not seen at 8:00 PM.",
      "eliminated": [],
      "remaining": [
        "Priya",
        "Maya"
      ],
      "worlds_left": 272,
      "from": "Casey"
    },
    {
      "clue_id": "d3p3",
      "day": 3,
      "player": 3,
      "text": "Maya was either on the Porch or in the Boathouse.",
      "eliminated": [
        "Maya"
      ],
      "remaining": [
        "Priya"
      ],
      "worlds_left": 64,
      "from": "Drew"
    }
  ],
  "votes": [
    {
      "player": "Alex",
      "suspect": "Priya",
      "correct": true
    },
    {
      "player": "Blake",
      "suspect": "Priya",
      "correct": true
    },
    {
      "player": "Casey",
      "suspect": "Maya",
      "correct": false
    },
    {
      "player": "Drew",
      "suspect": "Priya",
      "correct": true
    }
  ],
  "stats": {
    "worlds_total": 1728000,
    "worlds_public": 345600,
    "worlds_left": 64,
    "candidates_by_day": [
      4,
      3,
      1
    ],
    "seed": 7
  }
};

// Clue variants: template stories (Fact hidden, it repeats the story) and
// LLM-style stories (Fact shown), plus a clue without a story.
const fact = { kind: "demo" };

export const clues: Record<string, Clue> = {
  messageNew: {
    id: "d2p0", day: 2, from: "Alex", format: "Text message", fact,
    text: "Leo was seen at either 7:30 PM or 9:00 PM.",
    story: "Text from Rosa, the caretaker: \"Leo walked past with his guitar case. Either half seven or nine, I'd had a glass of rosé.\"",
  },
  photoTemplate: {
    id: "d1p0", day: 1, from: "Alex", format: "Photo caption", fact,
    text: "Jordan was not seen at 7:00 PM.",
    story: "Caption on a blurry group-chat photo: Jordan was not seen at 7:00 PM.",
  },
  receiptTemplate: {
    id: "d2p0r", day: 2, from: "Alex", format: "Receipt note", fact,
    text: "Leo was seen at either 7:30 PM or 9:00 PM.",
    story: "Handwritten on the back of a gas-station receipt: Leo was seen at either 7:30 PM or 9:00 PM.",
  },
  receiptStory: {
    id: "d2p1", day: 2, from: "Blake", format: "Receipt note", fact,
    text: "The person in the Loft had a fishing rod.",
    story: "LAKE WENDELL BAIT & TACKLE\nFishing rod rental ...... $15.00\nPicked up for: the Loft\nThank you, come again",
  },
  guestbookStory: {
    id: "d3p1", day: 3, from: "Blake", format: "Guestbook entry", fact,
    text: "The person in the Sunroom was seen earlier than Jordan.",
    story: "Scribbled in the cabin guestbook: \"Whoever had the Sunroom beat Jordan there, he showed up late as always.\"",
  },
  noStory: {
    id: "d1p2", day: 1, from: "Casey", format: null, fact,
    text: "Sam had either a flashlight or a deck of cards.",
    story: null,
  },
  sharedOverheard: {
    id: "d1p3", day: 1, from: "Drew", format: "Overheard on the dock", fact,
    text: "Jordan had either a flashlight or a deck of cards.",
    story: "Mr. Dunn from the next cabin remembers: \"Jordan was waving a flashlight around, or was it a deck of cards?\"",
  },
};
