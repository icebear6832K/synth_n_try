# Design Report: Event-Based Sound Synthesis Prototype

## 1. Overview

This project is an early prototype of an event-based sound synthesis and compositional structure framework. Its main purpose is to test a way of representing sound material as structured, vectorized events rather than as isolated notes, MIDI messages, or raw waveforms.

At the current stage, the project should be read as a conceptual and computational sketch. It demonstrates a system in which curves, pitch–amplitude values, intervals, and nested events are used to describe how sound comes into being through layered modifications.

## 2. Basic intention: vectorizing existence

The most fundamental intention behind the framework is to treat every sonic existence as something that can be vectorized.

In this context, pitch, amplitude, curves, and events are not merely audio parameters. They describe modifications applied to a more basic sonic existence-state. A curve or event can therefore be understood as an instruction that transforms an underlying event.

For example, a straight curve with amplitude `-2` can be interpreted as a description of “lowering the amplitude by 2” when applied to a more basic event. The system assumes a default existence-state, such as no pitch change and no amplitude change, and applies these vectorized modifications during rendering.

This makes the framework conceptually different from a typical synthesizer. Instead of beginning from predefined notes or instruments, it begins from abstract event modification.

## 3. Pitch–amplitude point representation

The basic unit is a pitch–amplitude point, represented by `PAPoint`.

A `PAPoint` contains:

- pitch value
- amplitude value

During rendering, pitch is converted to frequency through a semitone-like exponential mapping, while amplitude is converted through an exponential amplitude mapping. This allows musical pitch motion and amplitude scaling to be expressed in compact vector form.

The pitch–amplitude point functions as the local state of a sound event.

## 4. Curves as low-level transformations

`CurveValue` is a lower-level object than `Event`. It describes how pitch–amplitude values change across normalized time.

The current system includes several curve forms:

- `FixedValue`: a constant value;
- `LinearValue`: a direct interpolation between two values;
- `BezierCurve`: a shaped transition controlled by a Bezier segment;
- `CosineCurve`: periodic or oscillatory motion;
- `CroppedCurve`: a segment extracted from another curve;
- `JointCurve`: several curves connected in sequence;
- `OverlaidCurve`: several curves combined at the curve level.

At the curve level, the `*` operation overlays curve values and packages the result as another curve. After this operation, the event layer does not need to distinguish whether the curve was originally simple or internally overlaid. This creates a local layer of abstraction: curve composition is resolved before event composition.

## 5. Events as compositional units

`Event` is the main compositional unit of the framework.

An event may contain a single curve, multiple signal events, a composite structure, or an overlay of events. Events can be rendered into pitch–amplitude arrays, flattened into signal-level structures, shown visually, and synthesized into audio.

The main event operations include:

- `join`: sequentially connects events across time;
- `combine`: places different events together as simultaneous components;
- `overlay`: overlays multiple events;
- `loop`: repeats an event structure;
- `grow`: raises an event to a higher structural scale.

The difference between `join` and `combine` corresponds to a basic compositional distinction. `join` handles homogeneous or continuous objects unfolding over time. `combine` handles heterogeneous objects stacked or co-present within the same larger event.

## 6. Relative intervals as time structure

The interval system is designed to make time itself compositional.

Instead of only using fixed absolute start and end times, the system includes relative intervals and reference points. A relative interval can be mapped into another interval, allowing internal event structures to preserve their proportions while being placed inside a larger event.

This is important because an event may contain smaller events, and each smaller event may itself contain further internal structures. The time interval of an event therefore becomes part of the event grammar.

The original design direction suggests that interval logic could eventually be integrated even more deeply with event logic, so that intervals themselves behave like event-like structural objects.

## 7. Scale and `grow()`

The `grow()` mechanism is intended to mark and compare event scale.

In electroacoustic composition, a single “sound” may already contain many internal components: harmonic arrangements, internal energy envelopes, micro-oscillations, noise textures, and transient details. Such structures belong to an internal scale of the sound. The sound as a compositional object belongs to a higher scale.

The `layer_tag` and `grow()` design attempt to make this distinction explicit.

For example, an event describing internal sonic change may need to act on each sound inside a larger event, rather than acting on the entire larger event as one object. In that situation, event scale has to be represented, compared, and transformed.

The current implementation only partially realizes this intention, but the conceptual direction is important for understanding the project.

## 8. Current implemented model

The current implementation mainly realizes this model:

```text
T → (P, A)
```

That means each time point maps to a pitch–amplitude pair.

This supports tonal, gestural, and trajectory-based sound events: glissandi, amplitude envelopes, shaped transitions, oscillations, and layered pitch–amplitude motions.

A later extension would address this model:

```text
T → (P → A)
```

In that model, each time point maps to a pitch/frequency distribution. This would allow noise fields, spectral surfaces, granular textures, and more complex electroacoustic materials to be represented directly.

## 9. Current architecture

The main files are:

- `pAPoint.py`: pitch–amplitude vector objects;
- `curveValue.py`: fixed, linear, Bezier, cosine, cropped, joint, and overlaid curves;
- `bezierCalculator.py`: Bezier segment calculation for shaped transitions;
- `interval.py`: absolute intervals, relative intervals, and reference-point operations;
- `event.py`: signal events, composite events, overlaid events, rendering, visualization, and synthesis;
- `synth.py`: low-level sine-wave generation and WAV export;
- `arrStruct.py`: an experimental array-structure helper.

## 10. Known prototype limitations

The code is currently an exploratory prototype. Several aspects remain unfinished or need future cleanup:

- some functions are conceptually designed but not fully tested;
- naming is optimized for personal experimentation rather than public use;
- some methods likely require bug fixes before stable reuse;
- event layering and scale comparison are only partially implemented;
- the spectral/noise-field side of the event model is not yet implemented;
- documentation and examples need to be expanded if the project becomes a reusable library.

## 11. Suitable project description

A concise public-facing description would be:

> An experimental event-based sound synthesis framework that represents sonic material as vectorized pitch–amplitude trajectories, composable curves, nested time intervals, and layered event structures.

A more research-oriented description would be:

> This project explores how sound can be modeled as an abstract event structure before being rendered as audio. It treats pitch, amplitude, time intervals, curves, overlays, and scale layers as composable descriptions of sonic existence, aiming toward a broader framework for event-based electroacoustic composition.