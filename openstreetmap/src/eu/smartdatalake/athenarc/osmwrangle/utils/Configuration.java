/*
 * @(#) Configuration.java 	 version 1.8   2/5/2019
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
package eu.smartdatalake.athenarc.osmwrangle.utils;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;
import java.util.logging.Level;

/**
 * Parser of user-specified configuration files to be used during transformation of geospatial features into RDF triples.
 *
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 8/2/2013
 * Modified by: Panagiotis Kalampokis, 8/05/2019
 * Last modified: 8/05/2019
 */
public final class Configuration {

  /**
    Path to Atributes mapping File.
  */
  public String mapping_file;


  Assistant myAssistant;

  /**
   * Path to a properties file containing all parameters used in the transformation.
   */
  private String path;
  
  /**
   * Path to file(s) containing input dataset(s). 
   * Multiple input files (of exactly the same format and attributes) can be specified, separating them by ';' in order to activate multiple concurrent threads for their transformation.
   */
  public String inputFiles;
  
  /**
   * Path to a directory where intermediate files may be temporarily written during transformation.
   */
  public String tmpDir;
  
  /**
   * Path to the directory where output files will be written. By convention, output RDF files have the same name as their corresponding input dataset.
   */
  public String outputDir;
  
  /**
   * Default number of entities (i.e., records) to handle in each batch (applicable to STREAM and RML modes).
   */
  public int batch_size = 10;
  
  /**
   * String specifying the data source (provider) of the input dataset(s).
   */
  public String featureSource;

  
  /**
   * Spatial reference system (EPSG code) of the input dataset. If omitted, geometries are assumed in WGS84 reference system (EPSG:4326).
   * Example: EPSG:2100
   */
  public String sourceCRS;
  
  /**
   * Spatial reference system (EPSG code) of geometries in the output RDF triples. If omitted, RDF geometries will retain their original georeference (i.e., no reprojection of coordinates will take place).
   * Example: EPSG:4326
   */
  public String targetCRS;
 
 
  /**
   * Constructor of a Configuration object.
   * @param path   Path to a properties file containing all parameters to be used in the transformation.
   */
  public Configuration(String path) 
  {
	myAssistant = new Assistant();
    this.path = path;
    buildConfiguration();
    
  }

  /**
   * Loads the configuration from a properties file.
   */
  private void buildConfiguration() {

    Properties properties = new Properties();
    try {
      properties.load(new FileInputStream(path));
    } catch (IOException io) {
      System.out.println(Level.WARNING + " Problems loading configuration file: " + io);
    }
    initializeParameters(properties);
    
  }

  /**
   * Initializes all the parameters for the transformation from the configuration file.
   *
   * @param properties    All properties as specified in the configuration file.
   */
  private void initializeParameters(Properties properties) {

	 //File specification properties
	 if (!myAssistant.isNullOrEmpty(properties.getProperty("inputFiles"))) {
		 inputFiles = properties.getProperty("inputFiles").trim();
	 }
	 if (!myAssistant.isNullOrEmpty(properties.getProperty("outputDir"))) {
		 outputDir = properties.getProperty("outputDir").trim();
		 //Append a trailing slash to this directory in order to correctly create the path to output files
		 if ((outputDir.charAt(outputDir.length()-1)!=File.separatorChar) && (outputDir.charAt(outputDir.length()-1)!= '/'))
 			outputDir += "/";   //Always safe to use '/' instead of File.separator in any OS
	 }
	 if (!myAssistant.isNullOrEmpty(properties.getProperty("tmpDir"))) {
		 tmpDir = properties.getProperty("tmpDir").trim();
	 }
	 if (!myAssistant.isNullOrEmpty(properties.getProperty("mapping_file"))) {
	     mapping_file = properties.getProperty("mapping_file").trim();
	 }

	 //Number of entities (i.e., records) to handle in each batch; this actually controls how frequently the resulting RDF triples are written to file
	 if (!myAssistant.isNullOrEmpty(properties.getProperty("batchSize"))) {
		 try {
		 batch_size = Integer.parseInt(properties.getProperty("batchSize").trim());
		 //Apply the default value in case of invalid settings
		 if ((batch_size < 1) || (batch_size > 1000))
			 batch_size = 10;       
		 }
		 catch(Exception e) {
			 ExceptionHandler.abort(e, "Incorrect value set for batch size. Please specify a positive integer value in your configuration file.");
		 }		 
	 }
	 
    //Feature and attribute properties
    if (!myAssistant.isNullOrEmpty(properties.getProperty("featureSource"))) {
    	featureSource = properties.getProperty("featureSource").trim();
      }
	
	//Spatial reference system transformation properties
    if (!myAssistant.isNullOrEmpty(properties.getProperty("sourceCRS"))) {
    	sourceCRS = properties.getProperty("sourceCRS").trim();
      }
    if (!myAssistant.isNullOrEmpty(properties.getProperty("targetCRS"))) {
    	targetCRS = properties.getProperty("targetCRS").trim();
      }

  }

}
