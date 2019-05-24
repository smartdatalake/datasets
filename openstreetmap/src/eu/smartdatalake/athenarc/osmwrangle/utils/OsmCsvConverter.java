/*
 * @(#) OsmCsvConverter.java 	 version 1.8   2/5/2019
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

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.logging.Level;

import org.apache.commons.io.FilenameUtils;
import org.opengis.referencing.operation.MathTransform;

import com.fasterxml.jackson.databind.ObjectMapper;

import eu.smartdatalake.athenarc.osmwrangle.osm.OSMRecord;


/**
 * Provides a set of a streaming OSM records in memory that can be readily serialized into a CSV file.
 * CAUTION! This version also emits a .CSV output file that includes all tags identified in OSM (XML or PBF) files. 
 * DO NOT USE this version for transformation with other file formats.
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 26/9/2018
 * Modified by: Kostas Patroumpas, 27/9/2018
 * Modified by: Panagiotis Kalampokis, 8/05/2019
 * Last modified: 8/05/2019
 */

public class OsmCsvConverter {

	private static Configuration currentConfig;
	
	String DELIMITER = "|";
	
	//Used in performance metrics
	private long t_start;
	private long dt;
	private int numRec;            //Number of entities (records) in input dataset
	private int rejectedRec;       //Number of rejected entities (records) from input dataset after filtering

	private BufferedWriter csvWriter = null;

	//Attribute Map
	private HashMap<String, String> tagMap = new HashMap<>();
	private ArrayList<String> cols = new ArrayList<String>();

	public void ReadAttrMappingFile(Configuration config){

		Properties properties = new Properties();
		try {
			//Read Mapping Config File.
			properties.load(new FileInputStream(config.mapping_file));

			for (Map.Entry<Object, Object> entry : properties.entrySet()) {
				cols.add(entry.getKey().toString());
				String [] value_parts = entry.getValue().toString().replace("\"", "").trim().split(",");

				for (int i = 0; i < value_parts.length; i++) {
					tagMap.put(value_parts[i].trim(), entry.getKey().toString());
				}
			}

		} catch (IOException io) {
			System.out.println(Level.WARNING + " Problems loading configuration file: " + io);
		}
	}

	/**
	 * Constructs a OsmCsvConverter object that will conduct transformation at STREAM mode.	  	  
	 * @param config  User-specified configuration for the transformation process.
	 * @param outputFile  Output file that will collect resulting triples.
	 */
	public OsmCsvConverter(Configuration config, String outputFile) {
	    
	    currentConfig = config;       //Configuration parameters as set up by the various conversion utilities (CSV, SHP, DB, etc.)

		//Read Mapping File and build Collection.
		ReadAttrMappingFile(currentConfig);

	    //Initialize performance metrics
	    t_start = System.currentTimeMillis();
	    dt = 0;
	    numRec = 0;
	    rejectedRec = 0;
		
	    //Specify the CSV file that will collect the resulting tuples
	    try
	    {
	    	csvWriter = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(FilenameUtils.removeExtension(outputFile) + ".csv"), StandardCharsets.UTF_8));
	    	csvWriter.write(Constants.OUTPUT_CSV_HEADER + "|" + String.join("|", cols) + "|OTHER_TAGS");   //Custom header specified in Constants
	    	csvWriter.newLine();
	    }
	    catch (Exception e) {
			 ExceptionHandler.abort(e, "Output CSV file not specified correctly.");
	    }

	}

	/*
	* Formats a String escaping some special characters like: \n, \r, |
	* */
	public String formatString(String str){
		return str.replaceAll("\\r\\n|\\r|\\n", " ").replace("|", ";").trim();
	}


	/**
	 * Parses a single OSM record and streamlines the resulting triples (including geometric and non-spatial attributes).
	 * Applicable in STREAM transformation mode.
	 * Input provided as an individual record. This method is used for input from OpenStreetMap XML/PBF files.
	 * @param myAssistant  Instantiation of Assistant class to perform auxiliary operations (geometry transformations, auto-generation of UUIDs, etc.)
	 * @param rs  Representation of an OSM record with attributes extracted from an OSM element (node, way, or relation).
	 * @param classific  Instantiation of the classification scheme that assigns categories to input features.
	 * @param reproject  CRS transformation parameters to be used in reprojecting a geometry to a target SRID (EPSG code).
	 * @param targetSRID  Spatial reference system (EPSG code) of geometries in the output RDF triples.
	 */
	public void parse(Assistant myAssistant, OSMRecord rs, Classification classific, MathTransform reproject, int targetSRID)
	{
		try {
			//Formulate tags with double quotes in order to be properly recognized in post-processing
			ObjectMapper mapperObj = new ObjectMapper();

			Map tags = rs.getTagKeyValue();

			double lon = 0;
			double lat = 0;
			String category = "";

			if ((rs.getGeometry() != null) && (!rs.getGeometry().isEmpty()))
			{
				lon = myAssistant.getLongitude(rs.getGeometry());
				lat = myAssistant.getLatitude(rs.getGeometry());
			}

			//Skip OSM features with no category assigned according to their tags
			if (rs.getCategory() != null)
				category = rs.getCategory().replace("_", Constants.OUTPUT_CSV_DELIMITER);
			else
				return;

			ArrayList<String> outArr = new ArrayList<String>();
			outArr.add(rs.getID());
			outArr.add(rs.getName());
			outArr.add(category);
			outArr.add(Double.toString(lon));
			outArr.add(Double.toString(lat));
			outArr.add(Integer.toString(targetSRID));
			outArr.add(rs.getGeometry().toText());

			Map tagMapRec = new HashMap<String, String>();
			for(int i=0; i < cols.size(); i++){
				tagMapRec.put(cols.get(i), "");
			}


			for(Map.Entry<String, String> entry : tagMap.entrySet()) {
				String key = entry.getKey();
				String value = entry.getValue();

				String tagFieldValue =  tags.getOrDefault(key, "").toString();
				String existingValue = tagMapRec.get(value).toString();

				if(existingValue == ""){
					tagMapRec.put(value, tagFieldValue);
				}
				else{
					if(tagFieldValue != "")
						tagMapRec.put(value, existingValue + ";" + tagFieldValue);
				}

				tags.remove(key);
			}

			for(int i=0; i < cols.size(); i++){
				outArr.add(formatString(tagMapRec.get(cols.get(i)).toString()));
			}

			String othertags = formatString(mapperObj.writeValueAsString(rs.getTagKeyValue()));
			outArr.add(othertags);

			csvWriter.write(String.join("|", outArr));
			csvWriter.newLine();

			++numRec;
			//Periodically, collect RDF triples resulting from this batch and dump results into output file
			if (numRec % currentConfig.batch_size == 0)
			{
				myAssistant.notifyProgress(numRec);
			}

		} catch (Exception e) {
			System.out.println("Problem at element with OSM id: " + rs.getID() + ". Excluded from transformation.");
			rejectedRec++;
		}
	}


	/**
	 * Finalizes storage of resulting tuples into a file.	
	 * @param myAssistant  Instantiation of Assistant class to perform auxiliary operations (geometry transformations, auto-generation of UUIDs, etc.)
	 * @param outputFile  Path to the output file that collects RDF triples.
	 */	
	public void store(Assistant myAssistant, String outputFile) 
	{
		//******************************************************************
		//Close the file that will collect all tuples for the SLIPO Registry
		try {
			if (csvWriter != null)
				csvWriter.close();
		} catch (IOException e) {
			ExceptionHandler.abort(e, "An error occurred during creation of the output CSV file.");
		}
		//******************************************************************
		
	    //Measure execution time and issue statistics on the entire process
	    dt = System.currentTimeMillis() - t_start;
	    myAssistant.reportStatistics(dt, numRec, rejectedRec, currentConfig.targetCRS, outputFile);
	}
	  
}
