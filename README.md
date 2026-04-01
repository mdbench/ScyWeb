# ScyWeb
ScyWeb is a lightweight, deployable web application that lets users scramble and unscramble image files from a browser.

## Why is it called ScyWeb?
A scytale is an ancient Greek transposition cipher that utilizes a rod and parchment to scramble and unscramble messages. ScyWeb was developed to provide an image cipher experience using web technologies.

## Why do we need it?
Browsers have become state of the art applications. Many apps available on app stores can be made with wider compatibility for fractions of the code-base and energy. ScyWeb is only 345 lines of code at its base. Cybersecurity is getting harder and harder to achieve and an offline web app makes hacking virtually impossible, a breath of fresh air in a time of insecurity.

## Image scrambling
Lossless compression is not used on unscrambled images so the original image might be much smaller when compared to the new unscrambled image. Preliminary checks have identified scrambled images with lossless compression substantially smaller than images encrypted to plain text. A scrambled image is a much better option than encrypting images and a more secure option than encrypting an entire database or container of images and decrypting that database or container on application boot up. Image scrambling can be used in conjunction with current compression algorithms without causing issues. Unfortunately, the default mode does not show a proof of concept for a smaller scrambled file size when compared to an encrypted string but the alternative mode does. 

Important alternative method metrics have been listed below, showing alternative methods as a feasible replacement for encrypting images as strings:
![Image Scrambling Metrics - Scrambling versus Encryption](https://raw.githubusercontent.com/mdbench/ScyWeb/master/Screenshot-2026-03-29-7.57.16-PM.png)

An encrypted string of the original image [glacier_og_image_4503x3002.jpg](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/glacier_og_image_4503x3002.jpg) is 2.3MBs. You can see the methodology used to convert images to encrypted strings by visiting [the image to string converter demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebConverter.html). Without lossless compression, a scrambled version of the original image is 12.9MBs. With lossless compression, a scrambled version of the original image is 1.3MBs. This was surprising, as it indicated a scrambled image file size could actually be lower than the original copy. The alternative method uses block-chunking using similar nearest neighbors enhancing compression algorithims.

### Full compression test conducted (partially lossy). Results of tests below:
- [glacier_og_image_4503x3002.jpg fully compressed = 904KBs](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/FINAL_SIZE_MAX_COMPRESSION_glacier_og_image_4503x3002.jpg)
- [enc_glacier_og_image_4503x3002_scrambled.jpg fully compressed = 1.11MBs](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/FINAL_SIZE_MAX_COMPRESSION_ALTERNATIVE_METHOD_enc_glacier_og_image_4503x3002_scrambled.jpg)
    - A fully compressed alternative method scrambled image works but has some pixel re-replication problems (under development).

> Encrypted string is 100%+ larger than scrambled image. Difference between fully compressed original image and fully compressed scrambled image is 20%+ larger file size. Viability of scrambling images as a substitute for image to string encryption confirmed.

### General deciphering resistance
Below is a demo to prove scrambling is irreversible using visual heuristics without Pseudorandom Number Generator (PRNG) 256-bit key/number created from password hash with a caveat. Low quality images (600x300) with sharp edges and a small amount of colors (flags are the only archetype that meets this criteria) are easy to reconstruct when the image is known, making it possible for a similar image to partially but limitedly uncover portions of the image. However, high quality natural images are impossible to reconstruct and the test stops because continuing would likely crash your computer as the complexity increased. This doesn't mean it needs more compute. It means it will inevitably fail to compute because your hardware will fail before completion or you will die before it completes. You could run it anyways if you desired and you might get the top two rows of pixels reconstructed but it might take years and then not find any other rows for a milennia. 
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebImageTester.html)
    - The demo above calculates feasibility in unscrambling an image based on the original image using all open source, known information used in this project to conduct the scrambling. All modes have been immune to unscrambling reconstruction methods created by ChatGPT with the exception of low quality images that are non-natural graphics, like flags. If you test [the quantum ciphered LQ tester image](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/QUANTUM_enc_ImageReconstructionTesterIMG_LQ.jpg) with its [original uncipher version](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/ImageReconstructionTesterIMG_LQ.jpg), you will see it can unscramble the result! But, as soon as you move to natural images, especially higher quality ones, the complexity is too much for deciphering. Use [quantum cipher HQ tester image](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/QUANTUM_enc_ImageReconstructionTesterIMG_HQ.jpg) and [original uncipher version](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/ImageReconstructionTesterIMG_HQ.jpg) to see it stop early, admitting defeat!

### Quantum-resistant method
Quantum-proofing confirmed. Need third-parties to verify.
- Quantum resistance is a holistic approach, as the image must be indecipherable without the password but the image must also be quantum resistant from visual heuristic algos that attempt to coercively scramble the image back together.

> Encrypted string is 15%+ larger than scrambled image. Unfortunately, quantum resistant method is not compatible with compression, as it has too many pixel re-replication errors.

#### Success of image scrambling for tailored use cases is high. Unique viable use for making uninterrupted and uncompromised streaming, making a video stream unable to be modified in transit when delivered to users in real-time, offloading costs to user devices when it comes to unscrambling and re-rendering. Other uses include secure Bluerays, DVDs, and new age optical drives. Advanced use cases for movies delivered to theaters to prevent bootlegging. More use cases being tested but the sky is the limit.

## Movie scrambling
Lossless compression is not used on unscrambled movies so the original movie might be much smaller when compared to the new unscrambled movie. Scrambled movies are much bigger in their scrambled form than movies that use pixel information sharing, as this gets lost in the enciphering process. This is an area for further development. It means encrypted movies are smaller in size than scrambled movies. Below is a demo showing image scrambling being used on Big Buck Bunny at 1080 and then being converted back to unscrambled. There is no visual difference between the movies before and after scrambling and unscrambling them.
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebVideoTester.html)
- [Original Big Buck Bunny](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/Big_Buck_Bunny_1080_10s_30MB.mp4)
- [Unscrambled Big Buck Bunny](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/enc_BBB_Unscrambled.mp4)

## Due-Outs
- Fix pixel re-replication issue for fully compressed images on alternative method 
    - Severity: Low
- Fix pixel re-replication issue for fully compressed images on quantum method
    - Severity: High
- Add bulk image download for all files as a .zip option 
- Integrate image scrambling into HelioWeb

## Want to contribute?
Send me a pull request.

