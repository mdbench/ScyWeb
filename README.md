# ScyWeb
[ScyWeb](https://demos.matthewbenchimol.com/ScyWeb/ScyWeb.html) is a lightweight, deployable web application that lets users scramble and unscramble image files from a browser. The project has been extended to include things like: post quantum cryptography, audio-to-image re-filizing, and text-to-image re-filizing to secure and transform file systems in similar data formats without drastically increasing overhead. **Why would anyone want to make an mp3 or a txt file an image?**

1) Impossible to recover data without password
2) Immunity to file scanning by checksums and mime type
3) Easier file handling, as data can be processed the same way every time
4) Uninterrupted streams of data that cannot be compromised in transit

> See below for an academic paper on geometric stream ciphers in the world of quantum computing, working demos, proof of methods, proof of concepts, a structured overview of the process, evaluations of strengths, .

![ScyWeb Logo](https://raw.githubusercontent.com/mdbench/ScyWeb/master/ScyWebLogo.jpg)

## Working paper
- [Future academic submission as PDF](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/WorkingPaper.pdf)
- [LaTeX submission version](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/WorkingPaper.tex)
- [References with links & briefs](https://demos.matthewbenchimol.com/ScyWeb/ScyWebReferences.html)

## Why is it called ScyWeb?
A scytale is an ancient Greek transposition cipher that utilizes a rod and parchment to scramble and unscramble messages. ScyWeb was developed to provide an image cipher experience using web technologies.

## Why do we need it?
Browsers have become state of the art applications. Many apps available on app stores can be made with wider compatibility for fractions of the code-base and energy. ScyWeb is only 345 lines of code at its base. Cybersecurity is getting harder and harder to achieve and an offline web app makes hacking virtually impossible, a breath of fresh air in a time of insecurity.

## Image Databasing
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebDBMaker.html) a new ultra quantum resistant image database methodology. It allows you to batch NoSQL key queries. This demo showcases the methodology only and will be sold as a subscription for  personal and enterprise use.
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebSQLTester.html) a new quantum resistant image database methodology. It allows you to use SQL queries. This demo showcases the methodology only and will be sold as a subscription for  personal and enterprise use.
- [ScySDK](https://github.com/mdbench/ScyWeb/tree/main/sdk) is still under development as a working prototype with a [documentation and assessment hub](https://demos.matthewbenchimol.com/ScyWeb/sdk/adocs/ScySDKDocs.html) for developers looking to determine if ScySDK is right for their development project. This demo is free-to-use in accordance with [GPLv3 license](https://github.com/mdbench/ScyWeb?tab=GPL-3.0-1-ov-file) license.

### Success of image databasing is extremely high, as it makes database storage concerns virtually obsolete.

## Image scrambling
Lossy compression is not used on unscrambled images so the original image might be much smaller when compared to the new unscrambled image. Preliminary checks have identified scrambled images (alternative method) with lossless compression substantially smaller than images encrypted to plain text and even smaller when used with lossy compression methods, even though there is partial pixel loss (<5%) when lossy compression algos are used. A scrambled image is a much better option than encrypting images as strings and a more secure option than encrypting an entire database or container of images and decrypting that database or container on application boot up. Image scrambling (alternative method) can be used in conjunction with current compression algorithms without causing issues that are not already ocurring with endpoint decoding errors that go through a re-rendering processes to get back original image quality. Unfortunately, the default, quantum, and ultra quantum modes do not show a proof of concept for a smaller scrambled file size when compared to an encrypted strings. Only the alternative mode does.

Important alternative method metrics have been listed below, showing alternative method as a feasible replacement for encrypting images as strings:
![Image Scrambling Metrics - Scrambling versus Encryption](https://raw.githubusercontent.com/mdbench/ScyWeb/master/Screenshot-2026-03-29-7.57.16-PM.png)

An encrypted string of the original image [glacier_og_image_4503x3002.jpg](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/glacier_og_image_4503x3002.jpg) is 2.3MBs. You can see the methodology used to convert images to encrypted strings by visiting [the image to string converter demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebConverter.html). Without lossless compression, a scrambled version of the original image is 12.9MBs. With lossless and lossy compression, a scrambled version of the original image using the alternative method is 1.3MBs. This was surprising, as it indicated a scrambled image file size could be lower than the original copy. The alternative method uses block-chunking using similar nearest neighbors enhancing compression algorithims. A follow-up test to lossy compress the original and alternative method scrambled image is below.

### Full compression test conducted (lossy). Results of tests below:
- [glacier_og_image_4503x3002.jpg fully compressed = 904KBs](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/FINAL_SIZE_MAX_COMPRESSION_glacier_og_image_4503x3002.jpg)
- [enc_glacier_og_image_4503x3002_scrambled.jpg fully compressed = 1.11MBs](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/FINAL_SIZE_MAX_COMPRESSION_ALTERNATIVE_METHOD_enc_glacier_og_image_4503x3002_scrambled.jpg)
    - A fully compressed alternative method scrambled image works but has some pixel re-replication loss of <5%.

> Encrypted string is 100%+ larger than scrambled image. Difference between fully compressed original image and fully compressed scrambled image is 20%+ larger file size. Viability of scrambling images as a substitute for image to string encryption confirmed.

### General deciphering resistance
Below is a demo to prove scrambling is irreversible using visual heuristics without Pseudorandom Number Generator (PRNG) 256-bit key/number created from password hash with a caveat. Low quality images (600x300) with sharp edges and a small amount of colors (flags are the only archetype that meets this criteria) are easy to reconstruct when the image is known, making it possible for a similar image to partially but limitedly uncover portions of the image. However, high quality natural images are impossible to reconstruct and the test stops because continuing would likely crash your computer as the complexity increased. This doesn't mean it needs more compute. It means it will inevitably fail to compute because your hardware will fail before completion or you will die before it completes. You could run it anyways if you desired and you might get the top two rows of pixels reconstructed but it might take years and then not find any other rows for a milennia. 
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebImageTester.html)
    - The demo above calculates feasibility in unscrambling an image based on the original image using all open source, known information used in this project to conduct the scrambling. All modes have been immune to unscrambling reconstruction methods created by ChatGPT with the exception of low quality images that are non-natural graphics, like flags. If you test [the quantum ciphered LQ tester image](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/QUANTUM_enc_ImageReconstructionTesterIMG_LQ.jpg) with its [original uncipher version](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/ImageReconstructionTesterIMG_LQ.jpg), you will see it can unscramble the result! But, as soon as you move to natural images, especially higher quality ones, the complexity is too much for deciphering. Use [quantum cipher HQ tester image](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/QUANTUM_enc_ImageReconstructionTesterIMG_HQ.jpg) and [original uncipher version](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/ImageReconstructionTesterIMG_HQ.jpg) to see it stop early, admitting defeat!

### Quantum-resistant method
Quantum-proof method represents a significant increase in capability to defeat quantum computers using Grover's algo. Shor's algorithm is for integer factoring and discrete logarithms on quantum computers, working on numbers (encoded into qubits), not directly on images and this makes it easier to make images quantum proof, as Shor's algo is faster as an exponential speed up versus a quadratic one. All four methods are technically quantum proof, as each reaches far past grover's computational capability. Estimated qubits to beat 256-bit key is 1,200 to 2,500+ logical qubits or 14 million physical qubits. However, quantum resistance is a holistic approach, as the image must be indecipherable without the password but the image must also be quantum resistant from visual heuristic algos that attempt to coercively reconstruct the image back together.

Important quantum-resistant method metrics have been listed below, showing infeasibility of quantum brute-forcing to decipher image using visual heuristic algos using an available web [demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebImageTester.html):
![Proof of Quantum](https://raw.githubusercontent.com/mdbench/ScyWeb/master/Screenshot-2026-04-02-2.12.47-PM.png)

### Ultra Quantum-resistant method
Ultra quantum-proofing is a new concept where quantum methods cannot decipher or decrypt, even if the universe was a computer. Under the conditions of a simulation and simulacra, it would still be theoretically impossible to decipher or decrypt an ultra quantum scrambled image as long as the password was zero-knowledge or tied to an external process like a black box. This particular method is at the theoretically maximum for entropy and diffusion, making even quantum algos unable to detect a scrambled image is more than just white noise. 

#### Success of image scrambling for tailored use cases is high. Extremely good for private photos, messenging protocols, and archive storage on static quartz optical drives.

## Movie scrambling
Lossless compression is not used on unscrambled movies. Scrambled movies are much bigger in their scrambled form than movies that use pixel information sharing, as this gets lost in the enciphering process. This is an area for further development. It means encrypted movie strings are smaller in size than scrambled movies. Below is a demo showing image scrambling being used on Big Buck Bunny at 1080 and then being converted back to unscrambled. There is no visual difference between the movies before and after scrambling and unscrambling them. Further testing with altrrnative method is needed.
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebVideoTester.html)
- [Original Big Buck Bunny](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/Big_Buck_Bunny_1080_10s_30MB.mp4)
- [Unscrambled Big Buck Bunny](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/enc_BBB_Unscrambled.mp4)

### Success of movie scrambling for tailored use cases is high. Unique, viable use for making uninterrupted and uncompromised streaming, making a video stream unable to be modified in transit when delivered to users in real-time, offloading costs to user devices when it comes to unscrambling and re-rendering. Other uses include secure Bluerays, DVDs, and new age optical drives. Advanced use cases for movies delivered to theaters to prevent bootlegging.

## Streaming scrambling
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebVideoStreamTester.html)
- [Demo Stream DB](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/VIDEO_StreamTester.png)

### Success of streaming scrambler for tailored use cases is high. Unique, viable use for making pre-buffered streaming with auto-download for playback.

## Audio scrambling
The audio scrambling methodology takes an audio file, converts it to an image, and scrambles it using the default mode. It saves the resulting file with an mp3 extension, even though it is an image. When you add the scrambled audio file, unscrambling it, it is a perfect replication of the audio file, allowing you to store music in an encrypted format. Since music is already highly diffuse with high entropy, the default mode is sufficient to make the resulting scrambled audio image ultra quantum proof. This audio methodology also creates a 1:1 file size where the original audio file size is the exact size of the resulting scrambled image. You essentially lose nothing storage wise. Because it is unmodifiable without corrupting the audio image, this means it is impossible to modify your copy of whatever audio file you have.
- [Original MP3 Test File](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/ORIGINAL_AUDIO_solarflex-jazz-cafe-music-509921.mp3)
- [Scrambled MP3 Image with MP3 extension File](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/enc_SCRAMBLED_AUDIO_solarflex-jazz-cafe-music-509921_5287680.mp3)
- [Unscrambled MP3 Image Back to MP3 File](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/dec_UNSCRAMBLED_AUDIO_solarflex-jazz-cafe-music-509921.mp3)

### Success of audio scrambling for tailored use cases is extremely high. iTunes or Spotify could integrate this technology into their current database, making a music database compromise impossible. They could also integrate into their platforms, sending the audio image, coding right-before-use/just-in-time conversion, making music impossible to steal from a cache on all Operating Systems. This methodology would download a quantum proof image as a stable data-dependent cache and decrypt right before use in memory. Likely, trillion $ algorithm use case, as no compression lost. 

## Text scrambling
The text scrambling methodology takes a text file (all text/* files supported), converts it to an image, and scrambles it using the default mode. It saves the resulting file with a txt extension, even though it is an image. When you add the scrambled text file, unscrambling it, it is a perfect replication of the text file, allowing you to store text files in an encrypted format. Since text is already highly diffuse with high entropy, the default mode is sufficient to make the resulting scrambled text image ultra quantum proof. Unfortunately, this text methodology creates text files that are bigger than the originals.
- [Original TXT Test File](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/ORIGINAL_TEXT_test.txt)
- [Scrambled TXT Image with TXT extension File](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/enc_SCRAMBLED_TEXT_test.txt_16.txt)
- [Unscrambled TXT Image Back to TXT File](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/dec_UNSCRAMBLED_TEXT__test.txt)

### Success of text scrambling for tailored use cases is high. Storing text files as pictures could be used for website code files, rendered to user which then JS decrypts dynamically. Quantum resistant websites edited offline and uploaded as pictures render HTTPS and future web technologies obsolete. Website compromise would be meaningless without password, even if hacker got access to source code. Even passwords can be sent as pictures, making them impossible to steal with taffic sniffers, even if website was HTTP.

## Proofs, Feasibility, and the Quantum Decoherence Wall
- [Formal Mathematical Proofing Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebMathProof.html)
- [Reconstruction Feasibility Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebImageTester.html)
- [Explaining the Decoherence Wall Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebDecoherenceWall.html)

## Other Projects Under-Development
- [Compression Demo](https://demos.matthewbenchimol.com/ScyWeb/ScyWebCompressor.html)

## Due-Outs
- Fix pixel re-replication issue for fully compressed images on alternative method 
    - Severity: Low
- Fix pixel re-replication issue for fully compressed images on quantum method
    - Severity: High
- Add bulk image download for all files as a .zip option 
- Improve User Interface (UI) for Desktop/Mobile devices 
- Integrate image scrambling into HelioWeb
- Integrate music scrambling into PhonoWeb
- Calculate $ amount this project could earn
- Apply for patents (share patent numbers here)

## Want to contribute?
Send me a pull request.

