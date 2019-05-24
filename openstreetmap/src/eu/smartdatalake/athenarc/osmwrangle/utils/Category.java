/*
 * @(#) Category.java 	 version 1.8   30/4/2019
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
 * A category item in the classification scheme utilized in a dataset.
 *
 * @author Kostas Patroumpas
 * @version 1.8
 */

/* DEVELOPMENT HISTORY
 * Created by: Kostas Patroumpas, 7/11/2018
 * Last modified: 30/4/2019
 */

public class Category {
	
	private String UUID;             //A universally unique identifier (UUID) assigned to this category during transformation
	private String id;               //Original identifier of this category according to the classification scheme
	private String name;             //Name of the category as specified in the classification scheme
	private String parent;           //Original identifier of the parent of this category in the classification scheme
	
	/**
	 * Constructor of a Category object.
	 * @param UUID  A universally unique identifier (UUID) assigned to this category during transformation
	 * @param id  Original identifier of this category according to the classification scheme
	 * @param name  Name of the category as specified in the classification scheme
	 * @param parent Original identifier of the parent of this category in the classification scheme
	 */
	public Category(String UUID, String id, String name, String parent) {
		this.UUID = UUID.isEmpty() ? null : UUID;
		this.id = id.isEmpty() ? null : id;
		this.name = name.isEmpty() ? null : name;
		this.parent = parent.isEmpty() ? null : parent;
	}

	/**
	 * Provides the UUID of this category
	 * @return  The UUID assigned to this category
	 */
	public String getUUID() {
		return UUID;
	}

	/**
	 * Sets or updates the UUID of this category
	 * @param uuid   The UUID to be assigned to this category
	 */
	public void setUUID(String uuid) {
		this.UUID = uuid;
	}
	
	/**
	 * Provides the original identifier of this category
	 * @return   The original identifier of this category in the classification scheme
	 */
	public String getId() {
		return id;
	}
	
	/**
	 * Provides the original identifier of the parent of this category
	 * @return  The original identifier of the parent category in the classification scheme
	 */
	public String getParent() {
		return parent;
	}
	
	/**
	 * Provides the name of this category in the classification scheme
	 * @return  The name of this category
	 */
	public String getName() {
		return name;
	}
	
	/**
	 * Indicates whether a UUID has been assigned to this category
	 * @return  True if a UUID has been assigned to this category
	 */
	public boolean hasUUID() {
		return UUID != null;
	}
	
	/**
	 * Indicates whether this category has got an original identifier in the classification scheme
	 * @return  True if this category originally carries an identifier 
	 */
	public boolean hasId() {
		return id != null;
	}
	
	/**
	 * Indicates whether this category has a parent in the classification hierarchy
	 * @return  True if this category has a parent category in the classification scheme; False for top-tier categories
	 */
	public boolean hasParent() {
		return parent != null;
	}
	
	/**
	 * Indicates whether this category has got an original name in the classification scheme
	 * @return  True if this category originally carries a name 
	 */
	public boolean hasName() {
		return name != null;
	}
	
	/**
	 * Prints the attributes of this category as obtained from the classification scheme
	 * @return  A string that concatenates all original attributes of this category
	 */
	public String printContents() {
		return id + " " + name + " " + parent;
	}
}