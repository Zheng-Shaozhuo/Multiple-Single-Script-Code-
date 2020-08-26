package utils

import (
	"fmt"
	"strings"

	"database/sql"

	_ "github.com/go-sql-driver/mysql"
)

// DBWorker ...
type DBWorker struct {
	Dsn string
	Db  *sql.DB
}

// 内部通用方法提取
func commomOperate(db *sql.DB, sql string, args ...interface{}) (int64, int64) {
	var lastInsertID, rowsAffected int64
	stmt, err := db.Prepare(sql)
	defer stmt.Close()
	if err != nil {
		fmt.Println(err.Error())
		return lastInsertID, rowsAffected
	}
	result, err := stmt.Exec(args)
	if err != nil {
		fmt.Println(err.Error())
		return lastInsertID, rowsAffected
	}
	lastInsertID, _ = result.LastInsertId()
	rowsAffected, _ = result.RowsAffected()
	return lastInsertID, rowsAffected
}

// Insert 数据插入
func (dbw *DBWorker) Insert(table string, data map[string]interface{}) int64 {
	var keys []string
	var values []interface{}
	for k, v := range data {
		keys = append(keys, k)
		values = append(values, v)
	}
	sql := fmt.Sprintf("insert into %s (%s) values(%s)", table, strings.Join(keys, ","), strings.Trim(strings.Repeat("?,", len(keys)), ","))
	lastInsertID, _ := commomOperate(dbw.Db, sql, values...)
	return lastInsertID
}

// Query 数据查询
func (dbw *DBWorker) Query(table string, conds map[string]interface{}) []map[string]interface{} {
	var wheres []string
	var values []interface{}
	var result []map[string]interface{}
	for k, v := range conds {
		wheres = append(wheres, fmt.Sprintf("%s=?", k))
		values = append(values, v)
	}
	sql := fmt.Sprintf("select * from %s where %s", table, strings.Join(wheres, " and "))
	fmt.Println(sql)
	stmt, err := dbw.Db.Prepare(sql)
	defer stmt.Close()
	if err != nil {
		fmt.Println(err.Error())
		return result
	}
	rows, err := stmt.Query(values...)
	if err != nil {
		fmt.Println(err.Error())
		return result
	}
	columns, err := rows.Columns()
	if err != nil {
		fmt.Println(err.Error())
		return result
	}
	cache := make([]interface{}, len(columns))
	for i, _ := range cache {
		var t interface{}
		cache[i] = &t
	}
	for rows.Next() {
		err := rows.Scan(cache...)
		if err != nil {
			fmt.Println(err.Error())
			continue
		}
		item := make(map[string]interface{})
		for i, v := range cache {
			tv := *v.(*interface{})
			switch tv.(type) {
			case []uint8:
				item[columns[i]] = fmt.Sprintf("%s", tv)
			default:
				item[columns[i]] = tv
			}
		}
		result = append(result, item)
	}
	return result
}

// Update 数据修改
func (dbw *DBWorker) Update(table string, params, conds map[string]interface{}) bool {
	var sets, wheres []string
	var values []interface{}
	for k, v := range params {
		sets = append(sets, fmt.Sprintf("%s=?", k))
		values = append(values, v)
	}
	for k, v := range conds {
		wheres = append(wheres, fmt.Sprintf("%s=?", k))
		values = append(values, v)
	}
	sql := fmt.Sprintf("update %s set %s where %s", table, strings.Join(sets, ","), strings.Join(wheres, " and "))
	_, rowsAffected := commomOperate(dbw.Db, sql, values...)
	if int(rowsAffected) == 1 {
		return true
	}
	return false
}

// Delete 数据删除
func (dbw *DBWorker) Delete(table string, conds map[string]interface{}) bool {
	var wheres []string
	var values []interface{}
	for k, v := range conds {
		wheres = append(wheres, fmt.Sprintf("%s=?", k))
		values = append(values, v)
	}
	sql := fmt.Sprintf("delete from %s where %s", table, strings.Join(wheres, " and "))
	_, rowsAffected := commomOperate(dbw.Db, sql, values...)
	if int(rowsAffected) == 1 {
		return true
	}
	return false
}

// Init 初始化
func Init(dbw *DBWorker) *DBWorker {
	var err error
	dbw.Db, err = sql.Open("mysql", dbw.Dsn)
	if err != nil {
		panic(err.Error())
	}
	return dbw
}
