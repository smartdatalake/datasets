/*
 * @(#) Extractor.java	version 1.8  2/5/2019
 *
 * Copyright (C) 2013-2019 Information Management Systems Institute, Athena R.C., Greece.
 *
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package eu.smartdatalake.athenarc.osmwrangle;


import java.util.concurrent.ExecutionException;

import org.apache.commons.io.FilenameUtils;

import eu.smartdatalake.athenarc.osmwrangle.utils.Assistant;
import eu.smartdatalake.athenarc.osmwrangle.utils.Classification;
import eu.smartdatalake.athenarc.osmwrangle.utils.Configuration;
import eu.smartdatalake.athenarc.osmwrangle.utils.Constants;
import eu.smartdatalake.athenarc.osmwrangle.utils.ExceptionHandler;
import eu.smartdatalake.athenarc.osmwrangle.tools.OsmXmlToRdf;
import eu.smartdatalake.athenarc.osmwrangle.tools.OsmPbfToRdf;

/**
 * Entry point to OSMWrangle for converting spartial features extracted from OpenStreetMap files (either XML or PBF formats) into CSV
 * Execution command over JVM:
 *         JVM:   java -cp target/osmwrangle-1.8-SNAPSHOT.jar eu.smartdatalake.athenarc.osmwrangle.Extractor  <path-to-configuration-file>
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 23/3/2017
 * Modified: 3/11/2017; added support for system exit codes on abnormal termination
 * Modified: 8/11/2017; added support for preparing a classification scheme to be applied over entities
 * Modified: 21/11/2017; handling missing specifications for classification
 * Modified: 12/2/2018; handling missing specifications on georeferencing (CRS: Coordinate Reference Systems) 
 * Modified: 13/7/2018; advanced handling of interrupted or aborted tasks
 * Modified: 30/4/2019; simplified execution for extracting OSM features into CSV file
 * Last modified: 2/5/2019
 */
public class Extractor {

	static Assistant myAssistant;
	private static Configuration currentConfig;         //Configuration settings for the transformation
	static Classification classification = null;        //Classification hierarchy for assigning categories to features
	static int sourceSRID;                              //Source CRS according to EPSG 
	static int targetSRID;                              //Target CRS according to EPSG

	/**
	 * Main entry point to execute the transformation process.
	 * @param args  Arguments for the execution, including the path to a configuration file.
	 * @throws InterruptedException
	 * @throws ExecutionException
	 */
	public static void main(String[] args)  { 

		System.out.println(Constants.COPYRIGHT);
		
		String inFile;
		String outFile;
		
	    boolean failure = true;                        //Indicates whether transformation has failed to conclude
	    
	    if (args.length >= 0)  {

	    	//Specify a configuration file with properties used in the conversion
	    	currentConfig = new Configuration(args[0]);          //Argument like "./bin/shp_options.conf"
	    	
	    	myAssistant =  new Assistant(currentConfig);
	    	
			System.setProperty("org.geotools.referencing.forceXY", "true");
			
			//Check how many input files have been specified
			if (currentConfig.inputFiles != null)
			{
				inFile = currentConfig.inputFiles;                                                  //A SINGLE input OSM file name must be specified
				outFile = currentConfig.outputDir + FilenameUtils.getBaseName(inFile) + ".csv";     //CAUTION! Output file is always in CSV format
			}
			else {
				throw new IllegalArgumentException(Constants.INCORRECT_SETTING);
			}
						
			sourceSRID = 0;                                   //Non-specified, so...
			System.out.println(Constants.WGS84_PROJECTION);   //... all features are assumed in WGS84 lon/lat coordinates
			

			long start = System.currentTimeMillis();
			try {		
				//Apply data transformation according to the given input format
				if (inFile.toUpperCase().trim().endsWith("OSM")) {        	//OpenStreetMap data in XML format
					OsmXmlToRdf conv = new OsmXmlToRdf(currentConfig, inFile, outFile, sourceSRID, targetSRID);
					conv.apply();
					failure = false;
				}
				else if (inFile.toUpperCase().trim().endsWith("PBF")) {		//OpenStreetMap data in PBF format
					OsmPbfToRdf conv = new OsmPbfToRdf(currentConfig, inFile, outFile, sourceSRID, targetSRID);
					conv.apply();
					conv.close();
					failure = false;
				}	
				else {
					throw new IllegalArgumentException(Constants.INCORRECT_SETTING);
				}	
			} catch (Exception e) {
				ExceptionHandler.abort(e, Constants.INCORRECT_SETTING);      //Execution terminated abnormally
			}
			finally 
			{
				long elapsed = System.currentTimeMillis() - start;
				myAssistant.cleanupFilesInDir(currentConfig.tmpDir);             //Cleanup intermediate files in the temporary directory   
				if (failure) {
					System.out.println(myAssistant.getGMTime() + String.format(" Transformation process failed. Elapsed time: %d ms.", elapsed));
					System.exit(1);          //Execution failed in at least one task
				}
				else {
					System.out.println(myAssistant.getGMTime() + String.format(" Transformation process concluded successfully in %d ms.", elapsed));
					System.out.println("RDF results written into the following output files:" + outFile);
					//myAssistant.mergeFiles(outputFiles, "./test/output/merged_output.rdf");
					System.exit(0);          //Execution completed successfully
				}
			}		    
	    } 
	    else {
			System.err.println(Constants.INCORRECT_CONFIG); 
			System.exit(1);          //Execution terminated abnormally
	    }		    	 			    
	  }

}
