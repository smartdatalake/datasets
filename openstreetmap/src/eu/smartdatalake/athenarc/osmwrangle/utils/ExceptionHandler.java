/*
 * @(#) Configuration.java 	 version 1.7   24/2/2018
 *
 * Copyright (C) 2013-2019 Information Systems Management Institute, Athena R.C., Greece.
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
 * Handles exceptions raised by utilities. Issuing exit codes to the operation system.
 * @author Kostas Patroumpas
 * @version 1.7
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 3/11/2017
 * Last modified: 24/2/2018 
 */

public class ExceptionHandler {

	/**
	 * Prints warnings regarding issues raised during transformation.
	 * @param e  Exception raised in any stage of the transformation process.
	 * @param msg  Message to be issued along with the warning.
	 */
    public static void warn(Exception e, String msg) {
            e.printStackTrace();
            System.out.println(msg);
    }
  
    /**
     * Terminates execution of the transformation process due to an error.
     * @param e  Exception raised in any stage of the transformation process.
     * @param msg  Message to be issued along with the error.
     */
    public static void abort(Exception e, String msg) {
        e.printStackTrace();
        System.err.println("Transformation process terminated abnormally. " + msg);
        System.exit(1);                              //Issue signal to the operation system that execution terminated abnormally
    }
}
