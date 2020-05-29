# ALAuto_test
Please use ALAuto_test.py instead of ALAuto.py and have Tesseract installed.  
Launch ALAuto_test.py with -d to show debug messages.

### Known Issues
The retirement and enhancement modules are inherent from the upstream, which have been found unreliable. The filter configuration may not be applied in some conditions, so please be advised that using these modules may cause damage to your unlocked ships.

### 5/28

- Slightly optimized
- Added SIREN_ONLY_FIRST_6_SWIPES to config.ini

### 5/26

- Improved debug messages.


### FAQ

 - How SIREN_FIRST filter works?
 
    If the character is detected on the map - > Case (a)  
    If the character is not detected on the map - > Case (b)
      
    - Case (a): Get all reachable enemies and supplies sorted from nearest to farthest. (The ones the program thinks there are reachable, not the ground truth.) Then run the filters on them.  
    - Case (b): Get all enemies  and supplies  on the map. Then run the filters on them.
     
     The program doesn't have global view of the entire map but local view.  
