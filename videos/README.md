# Study Video and Quiz Questions

Every participant watches the same video. Participants are split into two groups: one group uses
a fidget toy (a squishy) while watching, and the other doesn't. Everyone then takes the same quiz,
so any difference in quiz scores between the groups comes from the fidget toy.

## The Video

| | |
| --- | --- |
| Title | The surprising reasons animals play dead |
| Educator | Tierney Thys (TED-Ed) |
| Length | 4:31 |
| Topic | Why animals like possums, chickens and sharks freeze and fake their own death |
| Link | [Watch on TED](https://www.ted.com/talks/tierney_thys_the_surprising_reasons_animals_play_dead) |

We play the video from the link above. The video file is not stored in this repo.

## Groups

| Group | Condition | Quiz form setting |
| --- | --- | --- |
| Fidget | Squishy toy in hand while watching | **Group 1**, **first quiz** |
| No fidget | No toy | **Group 2**, **first quiz** |

The quiz form was built for an earlier design where everyone did both conditions with two videos.
In that form, groups 1 and 2 both start with this video, with and without the fidget toy, so it
records the correct video and condition without any code changes. Only the first quiz is used.

Assign participants to the two groups in random order, in shuffled pairs: for each pair of
participants, flip a coin to decide who goes in which group. This keeps the groups the same size
and stops the condition from lining up with time of day.

## Running a Session

Total time is about 10 minutes per participant.

1. Give the participant an ID (P01, P02, …) and note their group in the session log.
2. Open `index.html` on the study laptop. Enter the participant ID (not their name) in the name
   field, choose **Group 1** (fidget) or **Group 2** (no fidget) and **first quiz**, and check that
   the start page shows "The surprising reasons animals play dead" and the right condition.
3. Fidget group only: hand them the squishy and tell them they can squeeze it while watching.
4. Play the video full screen at a fixed volume.
5. Take the squishy back. The participant presses **Begin** and takes the quiz.
6. The results CSV downloads automatically (for example `P01_VideoA_Assessment.csv`). Don't press
   **Start the next quiz**.

Use the same laptop, volume and setup for every session. Check beforehand that no ads play
before the video.

## Quiz Questions

10 multiple-choice questions, written from the video's content and spread across the whole video.
The quiz form reads them from [`../questions.js`](../questions.js) (video `A`); keep that file and
this table in step. The correct answers are also in [`answer_key.csv`](answer_key.csv) for scoring.

| # | Question | A | B | C | D | Correct |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | After a possum plays dead during an attack, about how long does it stay still before getting up and walking away? | About 1 minute | About 10 minutes | About 1 hour | About a whole day | **B** |
| 2 | Playing dead is also called "thanatosis." Where does that name come from? | The ancient Greek god of death | A Roman emperor who faked his death | The scientist who first described it | An ancient Egyptian god of sleep | **A** |
| 3 | Which baby animals improve their chances of surviving a cat by freezing while their siblings run around? | Ducklings | Baby rabbits | Quail chicks | Young lizards | **C** |
| 4 | What is "clipnosis"? | A way researchers calm sharks before tagging them | A beetle's reaction to low dopamine | A possum's foul-smelling defense | A calm state mother cats cause by pinching a kitten's neck | **D** |
| 5 | Most of the body processes behind playing dead come from the part of the nervous system that controls what? | Fight or flight | Resting and digesting | Vision and hearing | Memory and learning | **B** |
| 6 | Which flour beetles play dead more often? | Beetles with low dopamine levels | Beetles with high dopamine levels | The oldest beetles | The largest beetles | **A** |
| 7 | In an experiment with a stuffed hawk, when did chickens come out of their frozen state more quickly? | When the hawk was moved closer | When the lights were turned off | When other chickens were nearby | When the hawk's eyes were looking away | **D** |
| 8 | How does the sleeper cichlid fish use playing dead? | To hide from larger fish that hunt it | To attract a mate during breeding season | To ambush prey by looking like a rotting carcass | To rest safely on the lake floor at night | **C** |
| 9 | Why do male nursery spiders play dead? | To hide from birds that eat spiders | To avoid being eaten by the female | To trick insects into their web | To save energy during winter | **B** |
| 10 | By flipping a shark over and stroking its snout, about how long can researchers keep it still? | About 30 seconds | About 2 minutes | Up to 15 minutes | Up to 2 hours | **C** |
