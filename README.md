# synth_n_try

An experimental prototype for **event-based sound synthesis and compositional structure**.

這個專案是一套早期的聲音事件框架原型。它的核心目標不是製作一個成熟的音訊套件，而是嘗試把聲音、音高、振幅、曲線、時間區間與複合結構統一描述為可組合、可疊加、可尺度化的「事件」。

## Core idea

The framework treats sound as a vectorized event structure.

A sound event is not only a waveform or a note. It is a structured description of how a basic existence-state is modified across time. Pitch, amplitude, curve shapes, relative intervals, event layers, overlays, and composite structures are all treated as operations that can be applied to a more basic event.

In this model, a simple event such as a straight line with amplitude `-2` can be understood as an instruction that lowers the amplitude of a more basic event by two logarithmic units. During rendering, these abstract modifications are applied to a default sonic existence-state and converted into actual audio data.

## Current scope

The current code mainly implements the trajectory-based side of the system:

```text
T → (P, A)
```

That is, each time point maps to a pitch–amplitude pair. A later extension would be the spectral/noise-field side:

```text
T → (P → A)
```

where each time point maps to an amplitude distribution across pitch/frequency.

## Main components

### `PAPoint`

The basic pitch–amplitude vector.

- `pitch`: represented in semitone-like units.
- `amp`: represented in logarithmic amplitude units.
- Rendering converts pitch to frequency and amplitude to linear signal scale.

### `CurveValue`

A lower-level object describing parameter change.

Supported curve forms include:

- fixed value
- linear transition
- Bezier transition
- cosine/periodic transition
- cropped curve
- joint curve
- overlaid curve

At this layer, overlaying curves combines them inside the curve object itself. From the event layer, an overlaid curve is still just a curve.

### `Interval`

A relative and absolute time-interval system.

The framework supports intervals that can be mapped into parent intervals, making time itself compositional. This allows event structures to be described through nested reference systems rather than fixed absolute positions only.

### `Event`

The main compositional unit.

Events can be:

- rendered into pitch–amplitude arrays
- flattened into lower-level signal data
- joined sequentially
- combined simultaneously
- overlaid
- looped
- grown into higher structural scales
- synthesized into WAV output

The `grow` mechanism is intended to make event scale explicit. For example, a single electroacoustic “sound” may contain internal harmonic structure, energy envelopes, and micro-periodic changes. Such internal structure belongs to a smaller scale than the event representing the sound as a compositional object.

## Conceptual positioning

This project can be described as:

> An experimental event-based sound synthesis framework that represents sonic material as vectorized pitch–amplitude trajectories, composable curves, nested time intervals, and layered event structures.

It is best understood as a research prototype for compositional thinking rather than as a finished synthesizer library.

## Known limitations

This repository currently presents the project as an early prototype.

Known issues include:

- some code paths are not fully tested;
- public-facing naming and documentation are still minimal;
- several helper utilities may need to be reorganized;
- the spectral/noise-field model is not yet implemented;
- the scale/layer interaction intended by `grow()` is conceptually important but only partially realized.

## Design report

See [`docs/design-report.md`](docs/design-report.md) for a concise explanation of the framework, its current architecture, and its conceptual intention.