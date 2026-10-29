# Band Logbook

## 2026-10-29 Lab Session 2

> Goal: Take transmission data, plot it to see if it looks like a spread-out absorbance step change.
> 
> Approach: Follow all guidance available from Ocean Optics manual to perform the absorbance measurement. Paper lab manual, Appendix A Experiment Tutorials, Absorbance Experiments.
> 
> Lab data condition: lamp set to 60 V (maximum ~117), starting with one 10% ND filter (filter light outside of band, in case that disrupts sensitivity). Lamp turned on at 2:05pm. 
> 
> Temperature control started at 14:50. Start measuring the GaAs sample at a temperature of 20°C. The temperature takes at least 5 minutes to stabilize to within 0.5°C. Conduct measurements at temperature intervals of 20°C up to 120°C. 

Rough procedure
0. ~~Set temperature to 20°C.~~ (The room is already at 19.8°C now.)
0. Screw in blank holder.
1. Reference and dark measurement while that's happening.
2. Screw in GaAs sample holder. Wait for temperature to stabilize.
3. Take measurement, save text data, save plot, check reasonable.
4. Turn on the copper block heating.
5. Repeat at higher temperature points.

Question: are the ND filters also collimators?
- ND filter should not affect light focus, it is not lensed. Check the lab paper documents, and look at how they magnify or mirror an image. 
- They don't, they look to be flat filters. Confirm later with the Edmund Optics product listing.

Note: light at 60 V, one 10% ND filter is too bright. Minimum integration time is 3 ms. Cannot go below. Adding one 5% filter. Integration time is now about 35 ms. The measured intensity sees a periodic oscillation. Possibly AC signal. Try to average out by averaging over more samples. Online search suggests true AC coupling into measurement. Possible source: the halogen lamp brightness flickering with the AC power at 60 Hz.

Note: ~~to store the reference and dark spectra, click on the 'No Pre-processor, Absorbance Mode' layer, then File -> Store -> Store Dark Spectrum (Ctrl+D) or Store Reference Spectrum (Ctrl+R).~~ Use the 'save spectrum' icon in the toolbar, which allows you to save the reference, dark, and processed spectra to text file.
 
Note: First absorbance spectrum, absorbance seems to shoot up around 892 nm. 

Note: reference and dark spectra should've been captured with boxcar as well to smooth spectrum. Small random variation between scans will add noise to measurement. Set boxcar = 5 in the next attempt.

Note: Let's try measuring at 40°C, then 60°C, then keep this data for next time.

Note: SpectraSuite allows saving captures periodically. Can use this to automatically gather a LOT of captures to average over.

Note: Temperature rises remarkably quickly to 40°C, about 2 minutes time. Will take some time to stabilize.

Problem: absorbance does not start at zero. The GaAs sample holder seems to block more light than expected. Solution: subtract the baseline from the measurement, or add a level shift parameter to the curve fit. The absorbance is very flat at around 920-950 nm.

20: captured at 19.8°C and time about 15:30. Absorbance blows up at 892 nm.

40: captured at 43°C +- 0.5 and time about 15:40. Absorbance blows up at 900 nm. (the temperature went down while I was taking the measurement, I need to have the temp control dashboard and spectra suite next to each other. Taking a single capture right when I record the temperature will ensure consistency.)

60: captured at 60°C +- 0.1 and time about 15:59. Absorbance blows up at ~905 nm. The temperature control is just so much better now. Maybe the temperature controller has a problem with windup (integral error term)?

End by collecting 25 samples of 60°C data for possible comparison.

> Conclusion: I figured out some refinements to the spectroscopy data collection procedure which I need to incorporate into next week's full data collection. The three big ones are: enable boxcar smoothing with a small window size w=5 while capturing the reference and dark spectra, subtract the baseline absorbance to account for the difference in transmission between the GaAs sample holder and blank holder, and to use. Also, I have the option of saving many captures to file for further analysis. 
> 
> Next Steps: Complete the curve-fit and error analysis, and see if I get a result for the band-gap of GaAs which is consistent with published values. If so, otherwise I need to explain the difference. Then, finalize the procedural details and write myself a data collection procedure for Lab Session 3, which will let me complete all the data collection that I need during the lab time.
> 
> Temperature control started at 14:50. Start measuring the GaAs sample at a temperature of 20°C. The temperature takes at least 5 minutes to stabilize to within 0.5°C. Conduct measurements at temperature intervals of 20°C up to 120°C. 


## 2026-10-22 Lab Session 1

![task1-filter.PNG](task1-filter.PNG)

(Copy entry from notebook and Discourse post, and reformatted)