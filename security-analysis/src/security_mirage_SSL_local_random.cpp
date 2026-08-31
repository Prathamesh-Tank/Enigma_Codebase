// Copyright (C) 2021, Gururaj Saileshwar, Moinuddin Qureshi:
// Georgia Institute of Technology.
//
// Modified Mirage Monte Carlo model:
//   Tag store  : unchanged two-skew, load-aware placement.
//   Data store : round-robin SSL set selection followed by uniform-random
//                victim selection within the selected local data-store set.
//
// In this model, ballID is a PHYSICAL DATA-STORE SLOT:
//
//   ballID = data_set * DATA_STORE_WAYS + way.
//
// On every measured LLC installation, SSL chooses the next data-store set,
// local random replacement chooses one way in that set, the old line's tag is
// removed through balls[ballID], and the same physical slot is reused for the
// incoming line.

#include <stdio.h>
#include <assert.h>
#include <stdlib.h>

#include "mtrand.h"

/////////////////////////////////////////////////////
// COMMAND-LINE ARGUMENTS
/////////////////////////////////////////////////////
// argv[1] : EXTRA TAGS PER TAG-STORE SET (PER SKEW)
int EXTRA_BUCKET_CAPACITY = 5;

// argv[2] : NUMBER OF BILLION-INSTALLATION UNITS
int NUM_BILLION_TRIES = 1;

// argv[3] : RANDOM-NUMBER SEED
unsigned int myseed = 1;

/////////////////////////////////////////////////////
// CACHE CONFIGURATION
/////////////////////////////////////////////////////

// Mirage tag store: default logical occupancy is eight tags per bucket/skew.
#ifndef CUSTOM_BASE_WAYS_PER_SKEW
#define BASE_WAYS_PER_SKEW             (8)
#else
#define BASE_WAYS_PER_SKEW             (CUSTOM_BASE_WAYS_PER_SKEW)
#endif

#define NUM_SKEWS                      (2)

// 16 MiB LLC with 64-byte lines by default.
#ifndef CUSTOM_CACHE_SZ_BYTES
#define CACHE_SZ_BYTES                 (16ULL * 1024ULL * 1024ULL)
#else
#define CACHE_SZ_BYTES                 (CUSTOM_CACHE_SZ_BYTES)
#endif

#ifndef CUSTOM_LINE_SZ_BYTES
#define LINE_SZ_BYTES                  (64ULL)
#else
#define LINE_SZ_BYTES                  (CUSTOM_LINE_SZ_BYTES)
#endif

#define NUM_DATA_LINES                 (CACHE_SZ_BYTES / LINE_SZ_BYTES)

// Tag-store organization.
#define NUM_BUCKETS                    (NUM_DATA_LINES / BASE_WAYS_PER_SKEW)
#define NUM_BUCKETS_PER_SKEW           (NUM_BUCKETS / NUM_SKEWS)
#define BALLS_PER_BUCKET               (BASE_WAYS_PER_SKEW)

// Proposed data-store organization: 16-way local sets by default.
#ifndef CUSTOM_DATA_STORE_WAYS
#define DATA_STORE_WAYS                (16)
#else
#define DATA_STORE_WAYS                (CUSTOM_DATA_STORE_WAYS)
#endif

#define NUM_DATA_STORE_SETS            (NUM_DATA_LINES / DATA_STORE_WAYS)

// Tag-bucket capacity and occupancy-statistics range.
#ifndef CUSTOM_MAX_FILL
#define MAX_FILL                       (16)
#else
#define MAX_FILL                       (CUSTOM_MAX_FILL)
#endif

int SPILL_THRESHOLD = BALLS_PER_BUCKET + EXTRA_BUCKET_CAPACITY;

// Tie-breaking between equal-load tag candidates.
// 0: choose either skew uniformly at random.
// 1: always prefer skew 0.
#define BREAK_TIES_PREFERENTIALLY      (0)

/////////////////////////////////////////////////////
// EXPERIMENT SIZE
/////////////////////////////////////////////////////
// These override hooks permit short validation runs without changing the
// default Mirage-compatible command line or billion-installation semantics.
#ifndef CUSTOM_BILLION_TRIES
#define BILLION_TRIES                  (1000ULL * 1000ULL * 1000ULL)
#else
#define BILLION_TRIES                  (CUSTOM_BILLION_TRIES)
#endif

#ifndef CUSTOM_HUNDRED_MILLION_TRIES
#define HUNDRED_MILLION_TRIES          (100ULL * 1000ULL * 1000ULL)
#else
#define HUNDRED_MILLION_TRIES          (CUSTOM_HUNDRED_MILLION_TRIES)
#endif

#define PROGRESS_CHUNKS_PER_BILLION    (10)

/////////////////////////////////////////////////////
// TYPES AND COMPILE-TIME CHECKS
/////////////////////////////////////////////////////
typedef unsigned int uns;
typedef unsigned long long uns64;

static_assert((CACHE_SZ_BYTES % LINE_SZ_BYTES) == 0,
              "Cache size must be divisible by line size");
static_assert((NUM_DATA_LINES % DATA_STORE_WAYS) == 0,
              "Number of data lines must be divisible by data-store ways");
static_assert((NUM_BUCKETS % NUM_SKEWS) == 0,
              "Tag buckets must divide evenly across skews");
static_assert((NUM_BUCKETS * BALLS_PER_BUCKET) == NUM_DATA_LINES,
              "Tag-store average occupancy must equal number of data lines");
static_assert((PROGRESS_CHUNKS_PER_BILLION * HUNDRED_MILLION_TRIES) ==
                  BILLION_TRIES,
              "Ten progress chunks must equal one simulation unit");

/////////////////////////////////////////////////////
// EXPERIMENT STATE
/////////////////////////////////////////////////////

// For each tag-store bucket, number of resident tags.
uns64 bucket[NUM_BUCKETS];

// Reverse pointer for each physical data-store slot:
// balls[ballID] = tag-store bucket holding that slot's tag.
uns64 balls[NUM_DATA_LINES];

// Tag-store occupancy statistics.
uns64 bucket_fill_observed[MAX_FILL + 1];
uns64 stat_counts[MAX_FILL + 1];

// Spill statistics.
uns64 spill_count = 0;
uns64 cuckoo_spill_count = 0;

// SSL/local-random statistics.
uns64 ssl_next_data_set = 0;
uns64 data_set_select_count[NUM_DATA_STORE_SETS];
uns64 local_way_victim_count[DATA_STORE_WAYS];

bool init_buckets_done = false;
MTRand *mtrand = new MTRand();

/////////////////////////////////////////////////////
// TAG-STORE SPILL/CUCKOO HANDLING — UNCHANGED MODEL
/////////////////////////////////////////////////////

void spill_ball(uns64 index, uns64 ballID) {
  uns done = 0;

  // Undo the attempted insertion into the full bucket.
  bucket[index]--;

  while (done != 1) {
    uns64 spill_index;

    // Relocate to a random bucket in the opposite skew, as in the supplied
    // Mirage Monte Carlo implementation.
    if (index < NUM_BUCKETS_PER_SKEW)
      spill_index = NUM_BUCKETS_PER_SKEW +
                    mtrand->randInt((uns)(NUM_BUCKETS_PER_SKEW - 1));
    else
      spill_index = mtrand->randInt((uns)(NUM_BUCKETS_PER_SKEW - 1));

    if (bucket[spill_index] < (uns64)SPILL_THRESHOLD) {
      done = 1;
      bucket[spill_index]++;
      balls[ballID] = spill_index;
    } else {
      assert(bucket[spill_index] == (uns64)SPILL_THRESHOLD);
      index = spill_index;
      cuckoo_spill_count++;
    }
  }

  spill_count++;
}

/////////////////////////////////////////////////////
// TAG INSERTION — TWO RANDOM SKEWS + LOAD AWARENESS
/////////////////////////////////////////////////////

uns insert_ball(uns64 ballID) {
  const uns64 index1 =
      mtrand->randInt((uns)(NUM_BUCKETS_PER_SKEW - 1));
  const uns64 index2 =
      NUM_BUCKETS_PER_SKEW +
      mtrand->randInt((uns)(NUM_BUCKETS_PER_SKEW - 1));

  if (init_buckets_done) {
    assert(bucket[index1] <= MAX_FILL);
    assert(bucket[index2] <= MAX_FILL);
    bucket_fill_observed[bucket[index1]]++;
    bucket_fill_observed[bucket[index2]]++;
  }

  uns64 index;

  if (bucket[index2] < bucket[index1]) {
    index = index2;
  } else if (bucket[index1] < bucket[index2]) {
    index = index1;
  } else {
#if BREAK_TIES_PREFERENTIALLY == 0
    index = (mtrand->randInt(1) == 0) ? index1 : index2;
#elif BREAK_TIES_PREFERENTIALLY == 1
    index = index1;
#else
#error "Unsupported BREAK_TIES_PREFERENTIALLY value"
#endif
  }

  const uns retval = (uns)bucket[index];
  bucket[index]++;

  assert(ballID < NUM_DATA_LINES);
  assert(balls[ballID] == (uns64)-1);
  balls[ballID] = index;

  if (SPILL_THRESHOLD && retval >= (uns)SPILL_THRESHOLD) {
    // spill_ball() restores the full source bucket and places this ball in an
    // opposite-skew bucket; balls[ballID] is overwritten there.
    spill_ball(index, ballID);
  }

  return retval;
}

/////////////////////////////////////////////////////
// DATA-STORE VICTIM SELECTION
// ROUND-ROBIN SSL SET + LOCAL UNIFORM-RANDOM WAY
/////////////////////////////////////////////////////

uns64 remove_ball_ssl_local_random(void) {
  // Address-independent, round-robin set-selection logic (SSL).
  const uns64 selected_set = ssl_next_data_set;
  ssl_next_data_set++;
  if (ssl_next_data_set == NUM_DATA_STORE_SETS)
    ssl_next_data_set = 0;

  data_set_select_count[selected_set]++;

  // Uniform random replacement among ways local to the selected data set.
  const uns64 selected_way =
      mtrand->randInt((uns)(DATA_STORE_WAYS - 1));
  local_way_victim_count[selected_way]++;

  // ballID is the physical data-store slot selected for replacement.
  const uns64 ballID = selected_set * DATA_STORE_WAYS + selected_way;
  assert(ballID < NUM_DATA_LINES);

  // Follow the reverse pointer to invalidate/remove the old line's tag.
  assert(balls[ballID] != (uns64)-1);
  const uns64 bucket_index = balls[ballID];
  assert(bucket_index < NUM_BUCKETS);
  assert(bucket[bucket_index] != 0);

  bucket[bucket_index]--;
  balls[ballID] = (uns64)-1;

  // The incoming line will reuse exactly this physical slot.
  return ballID;
}

/////////////////////////////////////////////////////
// DISPLAY AND SANITY CHECKS
/////////////////////////////////////////////////////

void display_histogram(void) {
  uns64 s_count[MAX_FILL + 1];

  for (uns ii = 0; ii <= MAX_FILL; ii++)
    s_count[ii] = 0;

  for (uns64 ii = 0; ii < NUM_BUCKETS; ii++) {
    assert(bucket[ii] <= MAX_FILL);
    s_count[bucket[ii]]++;
  }

  printf("\nOccupancy: \t\t Count");
  for (uns ii = 0; ii <= MAX_FILL; ii++) {
    const double perc =
        100.0 * (double)s_count[ii] / (double)NUM_BUCKETS;
    printf("\nBucket[%2u Fill]: \t %llu \t (%4.2f)", ii,
           (unsigned long long)s_count[ii], perc);
  }
  printf("\n");
}

void sanity_check(void) {
  uns64 count = 0;

  for (uns64 ii = 0; ii < NUM_BUCKETS; ii++) {
    assert(bucket[ii] <= MAX_FILL);
    count += bucket[ii];
  }

  if (count != NUM_DATA_LINES) {
    printf("\n*** Sanity Check Failed: Total tags = %llu, expected %llu ***\n",
           (unsigned long long)count,
           (unsigned long long)NUM_DATA_LINES);
    assert(count == NUM_DATA_LINES);
  }

  // Every physical data slot must contain one valid line in steady state.
  for (uns64 ballID = 0; ballID < NUM_DATA_LINES; ballID++)
    assert(balls[ballID] != (uns64)-1);
}

void display_ssl_statistics(void) {
  uns64 min_set_count = data_set_select_count[0];
  uns64 max_set_count = data_set_select_count[0];
  uns64 total_set_selections = 0;

  for (uns64 set = 0; set < NUM_DATA_STORE_SETS; set++) {
    if (data_set_select_count[set] < min_set_count)
      min_set_count = data_set_select_count[set];
    if (data_set_select_count[set] > max_set_count)
      max_set_count = data_set_select_count[set];
    total_set_selections += data_set_select_count[set];
  }

  printf("\nSSL / Local-Random Replacement Statistics\n");
  printf("Total measured data-store replacements: %llu\n",
         (unsigned long long)total_set_selections);
  printf("Per-set SSL selections: min=%llu, max=%llu, difference=%llu\n",
         (unsigned long long)min_set_count,
         (unsigned long long)max_set_count,
         (unsigned long long)(max_set_count - min_set_count));

  printf("Local-way victim counts:\n");
  for (uns way = 0; way < DATA_STORE_WAYS; way++) {
    const double pct = total_set_selections
                           ? 100.0 * (double)local_way_victim_count[way] /
                                 (double)total_set_selections
                           : 0.0;
    printf("  Way[%2u]: %16llu (%7.4f%%)\n", way,
           (unsigned long long)local_way_victim_count[way], pct);
  }

  // Deterministic round robin guarantees at most one-count imbalance.
  assert(max_set_count - min_set_count <= 1);
}

/////////////////////////////////////////////////////
// INITIALIZATION
/////////////////////////////////////////////////////

void init_buckets(void) {
  assert(NUM_SKEWS * NUM_BUCKETS_PER_SKEW == NUM_BUCKETS);

  for (uns64 ii = 0; ii < NUM_BUCKETS; ii++)
    bucket[ii] = 0;

  for (uns64 ii = 0; ii < NUM_DATA_LINES; ii++)
    balls[ii] = (uns64)-1;

  for (uns ii = 0; ii <= MAX_FILL; ii++) {
    bucket_fill_observed[ii] = 0;
    stat_counts[ii] = 0;
  }

  for (uns64 set = 0; set < NUM_DATA_STORE_SETS; set++)
    data_set_select_count[set] = 0;

  for (uns way = 0; way < DATA_STORE_WAYS; way++)
    local_way_victim_count[way] = 0;

  spill_count = 0;
  cuckoo_spill_count = 0;
  ssl_next_data_set = 0;

  // Populate every physical data-store slot once. Initialization does not
  // contribute to measured SSL/replacement statistics, matching the original
  // simulator's full-cache steady-state initialization.
  for (uns64 ballID = 0; ballID < NUM_DATA_LINES; ballID++)
    insert_ball(ballID);

  sanity_check();
  init_buckets_done = true;
}

/////////////////////////////////////////////////////
// ONE MEASURED LLC INSTALLATION
/////////////////////////////////////////////////////

uns remove_and_insert(void) {
  // 1. SSL selects next data set.
  // 2. Local random replacement selects one way in that set.
  // 3. Remove old tag through reverse pointer.
  // 4. Reuse same physical data slot and install new tag via power-of-two.
  const uns64 ballID = remove_ball_ssl_local_random();
  const uns res = insert_ball(ballID);

  if (res <= MAX_FILL) {
    stat_counts[res]++;
  } else {
    printf("Overflow: destination tag bucket occupancy %u exceeds MAX_FILL=%u\n",
           res, (uns)MAX_FILL);
    exit(EXIT_FAILURE);
  }

  return res;
}

/////////////////////////////////////////////////////
// MAIN
/////////////////////////////////////////////////////

int main(int argc, char *argv[]) {
  assert((argc == 4) &&
         "Need 3 arguments: EXTRA_BUCKET_CAPACITY, BN_INSTALLATIONS, SEED");

  EXTRA_BUCKET_CAPACITY = atoi(argv[1]);
  NUM_BILLION_TRIES = atoi(argv[2]);
  myseed = (unsigned int)atoi(argv[3]);
  SPILL_THRESHOLD = BASE_WAYS_PER_SKEW + EXTRA_BUCKET_CAPACITY;

  assert(EXTRA_BUCKET_CAPACITY >= 0);
  assert(NUM_BILLION_TRIES >= 1);
  assert(SPILL_THRESHOLD <= MAX_FILL);
  assert(DATA_STORE_WAYS >= 1);

  const uns64 total_measured_installs =
      (uns64)NUM_BILLION_TRIES * (uns64)BILLION_TRIES;

  printf("Cache Configuration: %llu MiB, %d tag skews, "
         "%d average tags/bucket/skew\n",
         (unsigned long long)(CACHE_SZ_BYTES / 1024ULL / 1024ULL),
         NUM_SKEWS, BASE_WAYS_PER_SKEW);
  printf("Tag Store: %llu total buckets, %llu buckets/skew, "
         "spill threshold=%d\n",
         (unsigned long long)NUM_BUCKETS,
         (unsigned long long)NUM_BUCKETS_PER_SKEW,
         SPILL_THRESHOLD);
  printf("Data Store: %llu sets x %d ways = %llu lines\n",
         (unsigned long long)NUM_DATA_STORE_SETS,
         DATA_STORE_WAYS,
         (unsigned long long)NUM_DATA_LINES);
  printf("Replacement: round-robin SSL set selection + "
         "uniform local-random way victim\n");
  printf("Simulation Parameters: INSTALLATIONS=%llu, SEED=%u\n\n",
         (unsigned long long)total_measured_installs, myseed);

  mtrand->seed(myseed);
  init_buckets();
  sanity_check();

  printf("Starting -- (dot printed every %llu installations)\n",
         (unsigned long long)HUNDRED_MILLION_TRIES);

  for (uns64 bn_i = 0; bn_i < (uns64)NUM_BILLION_TRIES; bn_i++) {
    for (uns64 chunk = 0; chunk < PROGRESS_CHUNKS_PER_BILLION; chunk++) {
      for (uns64 ii = 0; ii < HUNDRED_MILLION_TRIES; ii++)
        remove_and_insert();

      printf(".");
      fflush(stdout);
    }

    sanity_check();
    printf(" %lluBn\n", (unsigned long long)(bn_i + 1));
    fflush(stdout);
  }

  printf("\n\nBucket-Occupancy Snapshot at End of Experiment\n");
  display_histogram();

  printf("\nDistribution of Bucket Occupancy Observed at the Two "
         "Candidate Tag Buckets\n");
  printf("\nOccupancy: \t\t %16s \t P(Bucket=k balls)", "Count");
  for (uns ii = 0; ii <= MAX_FILL; ii++) {
    const double perc =
        100.0 * (double)bucket_fill_observed[ii] /
        (NUM_SKEWS * (double)total_measured_installs);
    printf("\nBucket[%2u Fill]: \t %16llu \t (%9.6f%%)", ii,
           (unsigned long long)bucket_fill_observed[ii], perc);
  }

  printf("\n\nDistribution of Destination-Bucket Occupancy on "
         "Load-Aware Tag Insertion\n");
  printf("Balls in destination bucket (k) \t Insertions\n");
  for (uns ii = 0; ii <= MAX_FILL; ii++) {
    const double perc =
        100.0 * (double)stat_counts[ii] / (double)total_measured_installs;
    printf("%2u:\t\t\t\t %16llu (%9.6f%%)\n", ii,
           (unsigned long long)stat_counts[ii], perc);
  }

  printf("\nSpill Count: %llu (%9.6f%%)\n",
         (unsigned long long)spill_count,
         100.0 * (double)spill_count / (double)total_measured_installs);
  printf("Cuckoo Spill Count: %llu (%9.6f%%)\n",
         (unsigned long long)cuckoo_spill_count,
         100.0 * (double)cuckoo_spill_count /
             (double)total_measured_installs);

  display_ssl_statistics();

  return 0;
}
