package main
import "github.com/gin-gonic/gin"
func main(){ r:=gin.Default(); r.GET("/api/files/:id", func(c *gin.Context){ c.JSON(200, gin.H{"id":c.Param("id")}) }); }
