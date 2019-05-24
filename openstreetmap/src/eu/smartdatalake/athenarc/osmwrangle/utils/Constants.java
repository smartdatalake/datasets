/*
 * @(#) Constants.java 	 version 1.8   2/5/2019
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

/**
 * Constants utilized in the transformation and reverse transformation processes.
 *
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 8/2/2013
 * Modified by: Panagiotis Kalampokis, 8/05/2019
 * Last modified: 8/5/2019
 */
public class Constants {

  //REPLACEMENT value strings
  /**
   * Default line separator
   */
  public static final String LINE_SEPARATOR = "\n";      
  
  /**
   * String representation of UTF-8 encoding
   */
  public static final String UTF_8 = "UTF-8";           
  
  
  /**
   * Default delimiter of the CSV file used for registering features in the SLIPO Registry
   */
  public static final String OUTPUT_CSV_DELIMITER = "|";          

  /**
   * Default header with the attribute names of the CSV file used for output fatures
   */
  public static final String OUTPUT_CSV_HEADER = "ID|NAME|CATEGORY|SUBCATEGORY|LON|LAT|SRID|WKT";

  //Strings appearing in user notifications and warnings
  public static final String COPYRIGHT = "*********************************************************************\n*                      OSMWrangle version 1.8                        *\n* Developed by the Information Management Systems Institute.        *\n* Copyright (C) 2013-2019 Athena Research Center, Greece.           *\n* This program comes with ABSOLUTELY NO WARRANTY.                   *\n* This is FREE software, distributed under GPL license.             *\n* You are welcome to redistribute it under certain conditions       *\n* as mentioned in the accompanying LICENSE file.                    *\n*********************************************************************\n";
  public static final String INCORRECT_CONFIG = "Incorrect number of arguments. A properties file with proper configuration settings is required and must be placed in the resources folder.";
  public static final String INCORRECT_SETTING = "Incorrect or no value set for at least one parameter. Please specify a correct value in the configuration settings.";
  public static final String NO_REPROJECTION = "No reprojection to another coordinate reference system will take place.";
  public static final String WGS84_PROJECTION = "Input data is expected to be georeferenced in WGS84 (EPSG:4326).";
  
}
